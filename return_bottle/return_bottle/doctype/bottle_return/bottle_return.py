import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, flt, getdate, nowdate


def get_settings(pos_profile):
    """Get the configured return settings for this exact POS Profile."""
    profile = frappe.get_doc("POS Profile", pos_profile)
    if not cint(profile.get("custom_rb_enabled")):
        frappe.throw(_("Bottle returns are not enabled for POS Profile {0}").format(pos_profile))

    from return_bottle.pos_profile import validate_pos_profile

    validate_pos_profile(profile)
    return frappe._dict({
        "company": profile.company,
        "loyalty_program": profile.custom_rb_loyalty_program,
        "points_per_bottle": cint(profile.custom_rb_points_per_bottle),
        "bottle_item": profile.custom_rb_bottle_item,
        "warehouse": profile.custom_rb_empty_bottle_warehouse,
        "stock_valuation_rate": flt(profile.custom_rb_stock_valuation_rate),
        "reward_expense_account": profile.custom_rb_reward_expense_account,
        "stock_clearing_account": profile.custom_rb_stock_clearing_account,
    })


def check_pos_context(pos_profile, company):
    from erpnext.selling.page.point_of_sale.point_of_sale import check_pos_profile_access

    if not pos_profile:
        frappe.throw(_("POS Profile is required"))
    check_pos_profile_access(pos_profile)
    profile = frappe.get_doc("POS Profile", pos_profile)
    if profile.company != company or profile.disabled:
        frappe.throw(_("POS Profile is disabled or belongs to a different company"))
    opening = frappe.db.exists(
        "POS Opening Entry",
        {"user": frappe.session.user, "pos_profile": pos_profile, "company": company, "docstatus": 1,
         "pos_closing_entry": ["in", ["", None]]},
    )
    if not opening:
        frappe.throw(_("An open POS Opening Entry is required to receive bottles"))
    return profile


class BottleReturn(Document):
    def before_insert(self):
        self.cashier = frappe.session.user
        self.posting_date = nowdate()

    def validate(self):
        settings = get_settings(self.pos_profile)
        if self.company != settings.company:
            frappe.throw(_("POS Profile company does not match bottle return company"))
        check_pos_context(self.pos_profile, self.company)
        if not frappe.has_permission("Customer", "read", doc=self.customer):
            frappe.throw(_("Not permitted to use the selected customer"), frappe.PermissionError)

        quantity = cint(self.quantity)
        if not quantity or flt(self.quantity) != quantity or quantity < 0 or quantity > 10000:
            frappe.throw(_("Bottles Returned must be a whole number between 1 and 10000"))
        self.quantity = quantity
        self.points_per_bottle = cint(settings.points_per_bottle)
        self.total_points = quantity * self.points_per_bottle
        self.reward_amount = self.total_points
        self.bottle_item = settings.bottle_item
        self.warehouse = settings.warehouse
        self.stock_value = flt(quantity * flt(settings.stock_valuation_rate), 2)

        if self.is_new() and not self.client_request_id:
            frappe.throw(_("Request ID is required; use the POS return dialog"))
        if not self.is_new() and self.has_value_changed("cashier"):
            frappe.throw(_("Cashier cannot be changed"))

        customer_program = frappe.db.get_value("Customer", self.customer, "loyalty_program")
        if customer_program and customer_program != settings.loyalty_program:
            frappe.throw(_("Customer is enrolled in a different Loyalty Program"))

    def on_submit(self):
        settings = get_settings(self.pos_profile)
        # All three records are written inside the document's transaction.
        self._make_stock_entry(settings)
        self._make_journal(settings)
        self._award_points(settings)

    def before_cancel(self):
        if self.loyalty_point_entry:
            redeemed = frappe.db.sql(
                """select coalesce(sum(loyalty_points), 0) from `tabLoyalty Point Entry`
                   where redeem_against=%s""", self.loyalty_point_entry
            )[0][0]
            if flt(redeemed) < 0:
                frappe.throw(_("Cannot cancel: the customer's bottle reward has already been redeemed. Reverse its redemptions first."))

    def on_cancel(self):
        if self.loyalty_point_entry:
            frappe.get_doc("Loyalty Point Entry", self.loyalty_point_entry).delete(ignore_permissions=True)
        if self.journal_entry:
            journal = frappe.get_doc("Journal Entry", self.journal_entry)
            journal.flags.ignore_permissions = True
            journal.cancel()
        if self.stock_entry:
            stock = frappe.get_doc("Stock Entry", self.stock_entry)
            stock.flags.ignore_permissions = True
            stock.cancel()

    def _make_stock_entry(self, settings):
        entry = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "purpose": "Material Receipt",
            "company": self.company,
            "remarks": "Bottle Return " + self.name,
            "items": [{
                "item_code": self.bottle_item, "qty": self.quantity, "t_warehouse": self.warehouse,
                "basic_rate": flt(settings.stock_valuation_rate),
                "set_basic_rate_manually": 1,
                "allow_zero_valuation_rate": 1 if not flt(settings.stock_valuation_rate) else 0,
                "expense_account": settings.stock_clearing_account if flt(settings.stock_valuation_rate) else settings.reward_expense_account,
            }],
        })
        entry.insert(ignore_permissions=True)
        entry.submit()
        self.db_set("stock_entry", entry.name, update_modified=False)

    def _make_journal(self, settings):
        from erpnext import is_perpetual_inventory_enabled

        amount = flt(self.reward_amount, 2)
        valued = flt(self.stock_value, 2)
        if valued and not cint(is_perpetual_inventory_enabled(self.company)):
            frappe.throw(_("Perpetual inventory must be enabled for valued bottle returns"))

        cost_center = frappe.db.get_value("Loyalty Program", settings.loyalty_program, "cost_center")
        entries = []
        if valued:
            entries.append({"account": settings.stock_clearing_account, "debit_in_account_currency": valued})
        difference = flt(amount - valued, 2)
        if difference > 0:
            entries.append({
                "account": settings.reward_expense_account,
                "debit_in_account_currency": difference,
                "cost_center": cost_center,
            })
        entries.append({"account": frappe.db.get_value("Loyalty Program", settings.loyalty_program, "expense_account"),
                        "credit_in_account_currency": amount})
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "company": self.company,
            "posting_date": self.posting_date,
            "user_remark": "Bottle Return " + self.name,
            "accounts": entries,
        })
        je.insert(ignore_permissions=True)
        je.submit()
        self.db_set("journal_entry", je.name, update_modified=False)

    def _award_points(self, settings):
        customer = frappe.get_doc("Customer", self.customer)
        if not customer.loyalty_program:
            customer.db_set("loyalty_program", settings.loyalty_program, update_modified=False)
        expiry = cint(frappe.db.get_value("Loyalty Program", settings.loyalty_program, "expiry_duration"))
        entry = frappe.get_doc({
            "doctype": "Loyalty Point Entry",
            "customer": self.customer,
            "company": self.company,
            "loyalty_program": settings.loyalty_program,
            "loyalty_program_tier": "Bottle Return",
            "loyalty_points": self.total_points,
            "purchase_amount": 0,
            "posting_date": self.posting_date,
            "expiry_date": add_days(getdate(self.posting_date), max(1, expiry)),
            "invoice_type": self.doctype,
            "invoice": self.name,
        })
        entry.insert(ignore_permissions=True)
        self.db_set("loyalty_point_entry", entry.name, update_modified=False)
