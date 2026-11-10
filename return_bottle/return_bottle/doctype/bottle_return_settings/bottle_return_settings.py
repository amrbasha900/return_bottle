
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class BottleReturnSettings(Document):
    def validate(self):
        if not self.enabled:
            return

        required = {
            "company": _("Company"),
            "loyalty_program": _("Loyalty Program"),
            "bottle_item": _("Empty Bottle Item"),
            "warehouse": _("Return Warehouse"),
            "reward_expense_account": _("Rewards Expense Account"),
        }
        for key, label in required.items():
            if not self.get(key):
                frappe.throw(_("{0} is required to enable bottle returns").format(label))

        if cint(self.points_per_bottle) <= 0 or flt(self.points_per_bottle) != cint(self.points_per_bottle):
            frappe.throw(_("Points per bottle must be a positive integer"))

        if flt(self.stock_valuation_rate) < 0:
            frappe.throw(_("Stock valuation rate cannot be negative"))

        if frappe.db.get_value("Company", self.company, "default_currency") != "EGP":
            frappe.throw(_("Bottle rewards are denominated in EGP. Select an EGP company."))

        program = frappe.get_doc("Loyalty Program", self.loyalty_program)
        if program.company != self.company:
            frappe.throw(_("Loyalty Program must belong to the selected company"))
        if flt(program.conversion_factor) != 1:
            frappe.throw(_("Loyalty Program conversion factor must be 1 (one point = EGP 1)"))
        if not program.collection_rules:
            frappe.throw(_("Loyalty Program must have at least one collection rule"))
        if not program.expense_account:
            frappe.throw(_("Set the rewards liability account in Loyalty Program > Expense Account"))

        def check_account(account, root_type):
            details = frappe.db.get_value(
                "Account", account, ["company", "root_type", "is_group", "account_currency", "account_type"], as_dict=True
            )
            if not details or details.company != self.company or details.is_group or details.root_type != root_type:
                frappe.throw(_("{0} must be a non-group {1} account in the selected company").format(account, root_type))
            if details.account_currency != "EGP":
                frappe.throw(_("Account {0} must use EGP currency").format(account))
            return details

        check_account(program.expense_account, "Liability")
        check_account(self.reward_expense_account, "Expense")

        if flt(self.stock_valuation_rate):
            if flt(self.stock_valuation_rate) > cint(self.points_per_bottle):
                frappe.throw(_("Stock valuation per bottle cannot exceed its reward value"))
            if not self.stock_clearing_account:
                frappe.throw(_("Stock Clearing Account is required when stock valuation is greater than zero"))
            clearing = check_account(self.stock_clearing_account, "Asset")
            if clearing.account_type == "Stock":
                frappe.throw(_("Stock Clearing Account cannot be a Stock account"))
            from erpnext import is_perpetual_inventory_enabled
            if not cint(is_perpetual_inventory_enabled(self.company)):
                frappe.throw(_("Enable perpetual inventory for non-zero bottle valuation"))

        item = frappe.db.get_value(
            "Item", self.bottle_item,
            ["is_stock_item", "disabled", "has_serial_no", "has_batch_no", "is_fixed_asset"],
            as_dict=True,
        )
        if not item or not item.is_stock_item or item.disabled or item.has_serial_no or item.has_batch_no or item.is_fixed_asset:
            frappe.throw(_("Empty Bottle Item must be active, stock-managed and without serial/batch tracking"))

        warehouse = frappe.db.get_value("Warehouse", self.warehouse, ["company", "is_group"], as_dict=True)
        if not warehouse or warehouse.company != self.company or warehouse.is_group:
            frappe.throw(_("Return Warehouse must be a leaf warehouse in the selected company"))

        if not program.cost_center:
            frappe.throw(_("Set a Cost Center on the Loyalty Program for accounting"))
