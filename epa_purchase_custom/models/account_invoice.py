# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.multi
    def action_invoice_open(self):
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != "open")

        for invoice in to_open_invoices:
            if invoice.company_id.block_invoice_validation_exceeding_purchase:
                purchase_order = invoice.env["purchase.order"].search(
                    [("invoice_ids", "in", self.id)], limit=1
                )

                invoices = (
                    purchase_order.invoice_ids.filtered(
                        lambda x: x.state in ["open", "in_payment", "paid"]
                    )
                    + invoice
                )

                if (
                    invoice.type in ["in_invoice"]
                    and purchase_order
                    and sum(invoices.mapped("amount_total"))
                    > purchase_order.amount_total
                ):
                    raise UserError(
                        _(
                            "You cannot validate this invoice because the total amount "
                            "exceeds the total amount on the purchase order."
                        )
                    )

        return super().action_invoice_open()
