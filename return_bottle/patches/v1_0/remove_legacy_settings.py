"""Retire the obsolete site-wide Settings singleton.

No old warehouse is copied to POS Profiles: each branch must explicitly choose
its own bottle-return warehouse before enabling the feature.
"""

import frappe

from return_bottle.pos_profile import setup_pos_profile_fields


def execute():
    setup_pos_profile_fields()
    if frappe.db.exists("DocType", "Bottle Return Settings"):
        frappe.delete_doc(
            "DocType", "Bottle Return Settings", force=1, ignore_permissions=True
        )
