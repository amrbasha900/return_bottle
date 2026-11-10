(() => {
    const page = frappe.pages["point-of-sale"];
    if (!page || page.__bottle_return_hooked) return;
    page.__bottle_return_hooked = true;

    function current_pos(wrapper) {
        const pos = wrapper && wrapper.pos;
        if (!pos || !pos.pos_profile || !pos.company || !pos.page) return null;
        return pos;
    }

    async function open_dialog(pos) {
        const profile = pos.pos_profile;
        const config = await frappe.call({
            method: "return_bottle.api.get_pos_configuration",
            args: { pos_profile: profile },
        });
        const setup = config.message;
        if (!setup) return;

        const dialog = new frappe.ui.Dialog({
            title: __("Receive Empty Bottles"),
            fields: [
                {
                    label: __("Customer"), fieldname: "customer",
                    fieldtype: "Link", options: "Customer", reqd: 1,
                    default: pos.frm && pos.frm.doc && pos.frm.doc.customer || "",
                },
                {
                    label: __("Bottles Returned"), fieldname: "quantity",
                    fieldtype: "Int", reqd: 1, default: 1,
                    onchange: update_points,
                },
                {
                    label: __("Loyalty Points to Award"),
                    fieldname: "points", fieldtype: "Int", read_only: 1,
                    default: setup.points_per_bottle,
                },
                {
                    label: __("Receiving Warehouse"), fieldname: "receiving_warehouse",
                    fieldtype: "Data", read_only: 1, default: setup.warehouse,
                },
                {
                    label: __("POS Profile"), fieldname: "pos_profile",
                    fieldtype: "Data", read_only: 1, default: profile,
                },
            ],
            primary_action_label: __("Confirm Bottle Return"),
            primary_action: async (values) => {
                if (dialog.__submitting) return;
                if (!Number.isInteger(Number(values.quantity)) || Number(values.quantity) < 1 || Number(values.quantity) > 10000) {
                    frappe.msgprint(__("Enter a whole number of bottles (1 to 10000)"));
                    return;
                }
                dialog.__submitting = true;
                dialog.get_primary_btn().prop("disabled", true);
                // Keep this key for a retry after a connection error.
                dialog.__request_id = dialog.__request_id || (window.crypto && window.crypto.randomUUID ? window.crypto.randomUUID() : null);
                if (!dialog.__request_id) {
                    frappe.msgprint(__("This browser cannot generate a secure request identifier."));
                    dialog.__submitting = false;
                    dialog.get_primary_btn().prop("disabled", false);
                    return;
                }
                try {
                    const response = await frappe.call({
                        method: "return_bottle.api.receive_bottles",
                        type: "POST",
                        args: {
                            customer: values.customer, quantity: values.quantity,
                            pos_profile: profile, request_id: dialog.__request_id,
                        },
                        freeze: true,
                    });
                    const result = response.message;
                    if (!result) throw new Error(__("No return confirmation was received"));
                    dialog.hide();
                    frappe.show_alert({
                        message: __("Bottle Return {0}: {1} points awarded", [result.name, result.points]),
                        indicator: "green",
                    }, 7);
                } catch (error) {
                    console.error("Bottle return failed", error);
                    frappe.msgprint(__("Return was not confirmed. Review the error, then retry without closing this dialog."));
                } finally {
                    dialog.__submitting = false;
                    dialog.get_primary_btn().prop("disabled", false);
                }
            },
        });

        function update_points() {
            const count = Number(dialog.get_value("quantity")) || 0;
            dialog.set_value("points", Math.max(0, count) * setup.points_per_bottle);
            // A changed quantity after a failed call must not replay the same request ID.
            if (!dialog.__submitting) dialog.__request_id = null;
        }
        dialog.fields_dict.customer.df.onchange = () => {
            if (!dialog.__submitting) dialog.__request_id = null;
        };
        dialog.show();
    }

    function add_button(pos) {
        if (!pos || !pos.pos_profile || !pos.page || !pos.page.page_actions) return false;

        const $actions = pos.page.page_actions.find(".custom-actions");
        // ERPNext POS clears the header when prepare_fullscreen_btn runs.
        // Do not insert before the standard toolbar is ready.
        if (!$actions.length || !pos.page.page_actions.find(".fullscreen-btn").length) return false;
        if ($actions.find(".bottle-return-action").length) return true;

        const button = pos.page.add_button("تحصيل فارغ", () => {
            if (!Number(pos.settings && pos.settings.custom_rb_enabled)) {
                frappe.msgprint({
                    title: __("Bottle Returns Not Enabled"),
                    indicator: "orange",
                    message: __("Enable Bottle Returns for POS Profile {0} and reload Point of Sale.", [
                        pos.pos_profile,
                    ]),
                });
                return;
            }

            open_dialog(pos).catch((error) => {
                console.error("Bottle return configuration failed", error);
                frappe.msgprint(__("Unable to open Bottle Returns. Check POS Profile settings and user permissions."));
            });
        }, {
            btn_class: "btn-default bottle-return-action",
        });

        button.addClass("bottle-return-action");
        return true;
    }

    function hook_controller() {
        const Controller = window.erpnext && erpnext.PointOfSale && erpnext.PointOfSale.Controller;
        if (!Controller || !Controller.prototype) return false;
        if (Controller.prototype.__bottle_return_fullscreen_hooked) return true;
        const original = Controller.prototype.prepare_fullscreen_btn;
        if (typeof original !== "function") return false;

        Controller.prototype.prepare_fullscreen_btn = function (...args) {
            const result = original.apply(this, args);
            // This is called after ERPNext clears and recreates the POS actions.
            add_button(this);
            return result;
        };
        Controller.prototype.__bottle_return_fullscreen_hooked = true;
        return true;
    }

    // Also cover a POS controller that finishes loading before our hook attaches.
    function watch_pos(wrapper) {
        if (!wrapper) return;
        hook_controller();
        if (add_button(wrapper.pos)) return;

        if (wrapper.__bottle_return_poll) clearInterval(wrapper.__bottle_return_poll);
        let attempts = 0;
        wrapper.__bottle_return_poll = setInterval(() => {
            hook_controller();
            if (add_button(wrapper.pos) || ++attempts >= 150) {
                clearInterval(wrapper.__bottle_return_poll);
                wrapper.__bottle_return_poll = null;
            }
        }, 200);
    }

    const originalLoad = page.on_page_load;
    page.on_page_load = function (wrapper) {
        const result = originalLoad.call(this, wrapper);
        watch_pos(wrapper);
        return result;
    };

    const originalRefresh = page.refresh;
    page.refresh = function (wrapper) {
        const result = originalRefresh && originalRefresh.call(this, wrapper);
        watch_pos(wrapper);
        return result;
    };

    const originalShow = page.on_page_show;
    page.on_page_show = function (wrapper) {
        const result = originalShow && originalShow.call(this, wrapper);
        watch_pos(wrapper);
        return result;
    };
})();
