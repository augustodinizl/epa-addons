# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _default_mis_analytic_income_account_id(self):
        return self.env["ir.property"].get(
            "property_account_income_categ_id", "product.category"
        )

    @api.model
    def _default_mis_analytic_expense_account_id(self):
        return self.env["ir.property"].get(
            "property_account_expense_categ_id", "product.category"
        )

    epa_analytic_default_income_account_id = fields.Many2one(
        "account.account",
        default=_default_mis_analytic_income_account_id,
        readonly=False,
        string="Mis Builder Analytic Income Account",
        domain="[('deprecated', '=', False), ('company_id', '=', id)]",
    )
    epa_analytic_default_expense_account_id = fields.Many2one(
        "account.account",
        default=_default_mis_analytic_expense_account_id,
        readonly=False,
        string="Mis Builder Analytic Expense Account",
        domain="[ ('deprecated', '=', False), ('company_id', '=', id)]",
    )
