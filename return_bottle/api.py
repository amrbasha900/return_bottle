import uuid

import frappe
from frappe import _
from frappe.utils import cint

from return_bottle.return_bottle.doctype.bottle_return.bottle_return import (
    check_pos_context,
    get_settings,
)


@frappe.whitelist()
def get_pos_configuration(pos_profile):
    if not frappe.has_permission("Bottle Return", "create"):
        frappe.throw(_("Not permitted to receive bottles"), frappe.PermissionError)
    profile = check_pos_context(pos_profile)
    settings = get_settings(profile.name)
    return {
        "company": settings.company,
        "points_per_bottle": cint(settings.points_per_bottle),
        "loyalty_program": settings.loyalty_program,
        "warehouse": settings.warehouse,
    }


@frappe.whitelist(methods=["POST"])
def receive_bottles(customer, quantity, pos_profile, request_id):
    if not frappe.has_permission("Bottle Return", "create"):
        frappe.throw(_("Not permitted to receive bottles"), frappe.PermissionError)

    profile = check_pos_context(pos_profile)
    settings = get_settings(profile.name)
    try:
        rid = str(uuid.UUID(str(request_id)))
    except (ValueError, TypeError, AttributeError):
        frappe.throw(_("Invalid request ID"))

    existing = frappe.db.get_value("Bottle Return", {"client_request_id": rid}, "name")
    if existing:
        doc = frappe.get_doc("Bottle Return", existing)
        if doc.customer != customer or doc.pos_profile != pos_profile or cint(doc.quantity) != cint(quantity):
            frappe.throw(_("Request ID was already used with different values"))
        if doc.docstatus != 1:
            frappe.throw(_("Previous return is not submitted. Ask a supervisor to review it."))
        return {"name": doc.name, "points": doc.total_points, "existing": True}

    doc = frappe.get_doc({
        "doctype": "Bottle Return",
        "company": settings.company,
        "customer": customer,
        "quantity": quantity,
        "pos_profile": pos_profile,
        "client_request_id": rid,
    })
    doc.insert()
    doc.submit()
    return {"name": doc.name, "points": doc.total_points, "existing": False}
