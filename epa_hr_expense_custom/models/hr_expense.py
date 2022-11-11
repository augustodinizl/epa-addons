# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, models


class HrExpense(models.Model):

    _inherit = "hr.expense"

    @api.multi
    def _get_account_move_line_values(self):
        move_line_values_by_expense = super()._get_account_move_line_values()
        for expense_id, move_lines in move_line_values_by_expense.items():
            expense = self.browse(expense_id)
            for move_line in move_lines:
                if "date_maturity" in move_line.keys():
                    move_line["date_maturity"] = expense.sheet_id.maturity_date
        return move_line_values_by_expense
