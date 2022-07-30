# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, tools


class MisAccountAnalyticLine(models.Model):

    _inherit = "mis.account.analytic.line"

    @api.model_cr
    def init(self):
        default_account_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mis_builder_analytic_default_account_id")
        )
        tools.drop_view_if_exists(self._cr, "mis_account_analytic_line")
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW mis_account_analytic_line AS (
                SELECT
                    aal.id AS id,
                    'move_line' as line_type,
                    aal.id AS analytic_line_id,
                    aal.date as date,
                    CASE
                      WHEN aal.general_account_id is NULL THEN %s
                      ELSE aal.general_account_id
                    END as account_id,
                    aal.account_id as analytic_account_id,
                    aal.company_id as company_id,
                    'posted'::VARCHAR as state,
                    False as full_reconcile_id,
                    CASE
                      WHEN aal.amount >= 0.0 THEN aal.amount
                      ELSE 0.0
                    END AS credit,
                    CASE
                      WHEN aal.amount < 0 THEN (aal.amount * -1)
                      ELSE 0.0
                    END AS debit,
                    aal.amount as balance
                FROM
                    account_analytic_line aal
            )""",
            default_account_id,
        )
