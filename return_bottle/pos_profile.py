"""Per-POS-profile bottle return configuration (ERPNext v15)."""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import cint, flt

FIELDS = {
    "POS Profile": [
        {
            "fieldname": "custom_rb_section",
            "label": "Empty Bottle Returns",
            "fieldtype": "Section Break",
            "insert_after": "allow_partial_payment",
            "collapsible": 1,
        },
        {
            "fieldname": "custom_rb_enabled",
            "label": "Enable Bottle Returns",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "custom_rb_section",
        },
        {
            "fieldname": "custom_rb_empty_bottle_warehouse",
            "label": "Empty Bottle Warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "insert_after": "custom_rb_enabled",
            "description": "Stock received from this POS goes here, not to the normal POS selling warehouse.",
        },
        {
            "fieldname": "custom_rb_bottle_item",
            "label": "Empty Bottle Item",
            "fieldtype": "Link",
            "options": "Item",
            "insert_after": "custom_rb_empty_bottle_warehouse",
        },
        {
            "fieldname": "custom_rb_points_per_bottle",
            "label": "Reward Points per Bottle",
            "fieldtype": "Int",
            "default": "3",
            "insert_after": "custom_rb_bottle_item",
        },
        {
            "fieldname": "custom_rb_stock_valuation_rate",
            "label": "Empty Bottle Valuation (EGP)",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "custom_rb_points_per_bottle",
            "description": "Set the true recoverable inventory value. This is separate from the loyalty reward.",
        },
        {
            "fieldname": "custom_rb_column_break",
            "fieldtype": "Column Break",
            "insert_after": "custom_rb_stock_valuation_rate",
        },
        {
            "fieldname": "custom_rb_loyalty_program",
            "label": "Bottle Return Loyalty Program",
            "fieldtype": "Link",
            "options": "Loyalty Program",
            "insert_after": "custom_rb_column_break",
            "description": "Use the same programme across POS Profiles in one company to share customer points.",
        },
        {
            "fieldname": "custom_rb_reward_expense_account",
            "label": "Bottle Reward Expense Account",
            "fieldtype": "Link",
            "options": "Account",
            "insert_after": "custom_rb_loyalty_program",
        },
        {
            "fieldname": "custom_rb_stock_clearing_account",
            "label": "Bottle Stock Clearing Account",
            "fieldtype": "Link",
            "options": "Account",
            "insert_after": "custom_rb_reward_expense_account",
            "description": "Required only when Empty Bottle Valuation is greater than zero.",
        },
    ],
}


def setup_pos_profile_fields():
    """Idempotent, used at install and migrate. Does not overwrite profile values."""
    create_custom_fields(FIELDS, update=True)


def validate_pos_profile(doc, method=None):
    """Only bottle-enabled profiles need the additional settings."""
    if not cint(doc.get("custom_rb_enabled")):
        return

    if not doc.company:
        frappe.throw(_("Set a company on the POS Profile first."))

    required = {
        "custom_rb_empty_bottle_warehouse": _("Empty Bottle Warehouse"),
        "custom_rb_bottle_item": _("Empty Bottle Item"),
        "custom_rb_loyalty_program": _("Bottle Return Loyalty Program"),
        "custom_rb_reward_expense_account": _("Bottle Reward Expense Account"),
    }
    for field, label in required.items():
        if not doc.get(field):
            frappe.throw(_("{0} is required when bottle returns are enabled.").format(label))

    points = cint(doc.custom_rb_points_per_bottle)
    if points < 1 or flt(doc.custom_rb_points_per_bottle) != points:
        frappe.throw(_("Reward Points per Bottle must be a positive whole number."))

    rate = flt(doc.custom_rb_stock_valuation_rate)
    if rate < 0 or rate > points:
        frappe.throw(_("Empty Bottle Valuation must be between 0 and the reward per bottle."))

    currency = frappe.db.get_value("Company", doc.company, "default_currency")
    if currency != "EGP":
        frappe.throw(_("Bottle returns require an EGP company (1 point = EGP 1)."))

    warehouse = frappe.db.get_value(
        "Warehouse", doc.custom_rb_empty_bottle_warehouse, ["company", "is_group"], as_dict=True
    )
    if not warehouse or warehouse.company != doc.company or warehouse.is_group:
        frappe.throw(_("Empty Bottle Warehouse must be a non-group warehouse of this company."))

    item = frappe.db.get_value(
        "Item", doc.custom_rb_bottle_item,
        ["is_stock_item", "disabled", "has_serial_no", "has_batch_no", "is_fixed_asset"], as_dict=True
    )
    if not item or not item.is_stock_item or item.disabled or item.has_serial_no or item.has_batch_no or item.is_fixed_asset:
        frappe.throw(_("Empty Bottle Item must be an active stock item without serial or batch numbers."))

    program = frappe.get_doc("Loyalty Program", doc.custom_rb_loyalty_program)
    if program.company != doc.company or flt(program.conversion_factor) != 1:
        frappe.throw(_("Bottle Loyalty Program must belong to this company and convert 1 point to EGP 1."))
    if not program.collection_rules or not program.cost_center or not program.expense_account:
        frappe.throw(_("Configure the Loyalty Program's collection tier, cost center and liability account."))

    def check_account(name, root_type):
        account = frappe.db.get_value(
            "Account", name,
            ["company", "root_type", "is_group", "account_currency", "account_type"],
            as_dict=True,
        )
        if (
            not account
            or account.company != doc.company
            or account.root_type != root_type
            or account.is_group
            or account.account_currency != "EGP"
        ):
            frappe.throw(_("{0} must be a non-group EGP {1} account in this company.").format(name, root_type))
        return account

    check_account(program.expense_account, "Liability")
    check_account(doc.custom_rb_reward_expense_account, "Expense")

    if rate:
        from erpnext import is_perpetual_inventory_enabled

        if not cint(is_perpetual_inventory_enabled(doc.company)):
            frappe.throw(_("Enable perpetual inventory for non-zero bottle stock valuation."))
        if not doc.custom_rb_stock_clearing_account:
            frappe.throw(_("Bottle Stock Clearing Account is required for non-zero valuation."))
        clearing = check_account(doc.custom_rb_stock_clearing_account, "Asset")
        if clearing.account_type == "Stock":
            frappe.throw(_("Bottle Stock Clearing Account cannot be a Stock account."))
