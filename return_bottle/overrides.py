from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice


class BottleReturnPOSInvoice(POSInvoice):
    """Never award points for ordinary POS sales using the bottle-return programme.

    Preserve the standard ERPNext redemption path, including cancellation behavior.
    """

    def make_loyalty_point_entry(self):
        from frappe import db

        configured = db.get_single_value("Bottle Return Settings", "loyalty_program")
        enabled = db.get_single_value("Bottle Return Settings", "enabled")
        if enabled and configured and self.loyalty_program == configured:
            return
        return super().make_loyalty_point_entry()
