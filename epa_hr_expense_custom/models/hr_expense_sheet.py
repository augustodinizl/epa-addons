# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrExpenseSheet(models.Model):

    _inherit = "hr.expense.sheet"

    accounting_date = fields.Date("Date", default=fields.Date.context_today)
