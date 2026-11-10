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

    function add_button(wrapper) {
        const pos = current_pos(wrapper);
        if (!pos) return;
        const customActions = pos.page.page_actions.find(".custom-actions");
        if (customActions.find(".bottle-return-action").length) return;
        const button = pos.page.add_button(__("Return Bottles"), () => open_dialog(pos), {
            btn_class: "btn-default bottle-return-action",
            icon: "refresh-ccw",
        });
        button.addClass("bottle-return-action");
    }

    // Page hooks execute after the standard page script in Frappe's Page.load_assets.
    // POS loads asynchronously; wrap make_app before the first POS controller construction.
    function hook_controller() {
        const Controller = window.erpnext && erpnext.PointOfSale && erpnext.PointOfSale.Controller;
        if (!Controller || Controller.prototype.__bottle_return_hooked) return false;
        const oldMakeApp = Controller.prototype.make_app;
        Controller.prototype.make_app = function (...args) {
            const result = oldMakeApp.apply(this, args);
            add_button(this.page.wrapper);
            return result;
        };
        Controller.prototype.__bottle_return_hooked = true;
        return true;
    }

    const originalLoad = page.on_page_load;
    page.on_page_load = function (wrapper) {
        const result = originalLoad.call(this, wrapper);
        let attempts = 0;
        const timer = setInterval(() => {
            if (hook_controller()) {
                clearInterval(timer);
                add_button(wrapper);
            } else if (++attempts >= 100) {
                clearInterval(timer);
                console.warn("Bottle return: POS controller not available");
            }
        }, 100);
        return result;
    };
    const originalRefresh = page.refresh;
    page.refresh = function (wrapper) {
        const result = originalRefresh && originalRefresh.call(this, wrapper);
        add_button(wrapper);
        return result;
    };
})();
