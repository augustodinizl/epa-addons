# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, tools


class MisAccountAnalyticLine(models.Model):
    _inherit = "mis.account.analytic.line"

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, "mis_account_analytic_line")
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW mis_account_analytic_line AS (
                SELECT
                    aal.id AS id,
                    'move_line' AS line_type,
                    aal.id AS analytic_line_id,
                    aal.date AS date,
                    CASE
                      WHEN aal.general_account_id is NULL AND aal.amount >= 0 THEN
                        (SELECT epa_analytic_default_income_account_id
                        FROM res_company WHERE id = aal.company_id LIMIT 1)
                      WHEN aal.general_account_id is NULL AND aal.amount < 0 THEN
                        (SELECT epa_analytic_default_expense_account_id
                        FROM res_company WHERE id = aal.company_id LIMIT 1)
                      ELSE aal.general_account_id
                    END AS account_id,
                    aal.account_id AS analytic_account_id,
                    aal.company_id AS company_id,
                    'posted'::VARCHAR AS state,
                    False AS full_reconcile_id,
                    CASE
                      WHEN aal.amount >= 0.0 THEN aal.amount
                      ELSE 0.0
                    END AS credit,
                    CASE
                      WHEN aal.amount < 0 THEN (aal.amount * -1)
                      ELSE 0.0
                    END AS debit,
                    aal.amount AS balance
                FROM
                    account_analytic_line aal
            )"""
        )
