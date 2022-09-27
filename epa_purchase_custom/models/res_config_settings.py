# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    block_invoice_validation_exceeding_purchase = fields.Boolean(
        string="Block invoice validation exceeding purchase",
        readonly=False,
        related="company_id.block_invoice_validation_exceeding_purchase",
    )
