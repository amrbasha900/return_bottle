import frappe

from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice


class BottleReturnPOSInvoice(POSInvoice):
    """Keep standard redemption; disable earning for any bottle-return programme."""

    def make_loyalty_point_entry(self):
        if self.loyalty_program:
            programmes = frappe.get_all(
                "POS Profile",
                filters={
                    "custom_rb_enabled": 1,
                    "custom_rb_loyalty_program": self.loyalty_program,
                },
                pluck="name",
                limit=1,
            )
            if programmes:
                return

        return super().make_loyalty_point_entry()
