from odoo import models, api

class StockRequestOrder(models.Model):
    _inherit = 'stock.request.order'

    @api.multi
    def write(self, vals):
        res = super(StockRequestOrder, self).write(vals)
        if 'project_id' in vals:
            for record in self:
                record._update_location_and_analytic_account()
        return res

    @api.model
    def create(self, vals):
        record = super(StockRequestOrder, self).create(vals)
        record._update_location_and_analytic_account()
        return record

    def _update_location_and_analytic_account(self):
        if self.project_id:
            if self.project_id.location_dest_id:
                self.location_id = self.project_id.location_dest_id.id
            if self.project_id.analytic_account_id:
                analytic_account_id = self.project_id.analytic_account_id.id
                for line in self.stock_request_ids:
                    line.write({'analytic_account_id': analytic_account_id})
        else:
            self.location_id = False
            for line in self.stock_request_ids:
                line.write({'analytic_account_id': False})
