# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class FsmOrder(models.Model):

    _inherit = "fsm.order"

    @api.onchange("person_ids")
    def _onchange_person_ids(self):
        reserved_name_workers = []
        for person in self.person_ids:
            if not self.scheduled_date_end:
                domain = [
                    ("date_end", "=", None),
                    ("scheduled_date_start", "<=", self.scheduled_date_start),
                    ("scheduled_date_end", ">=", self.scheduled_date_start),
                    ("person_ids", "in", person.id),
                ]
            else:
                domain = [
                    ("date_end", "=", None),
                    ("scheduled_date_start", "<=", self.scheduled_date_end),
                    ("scheduled_date_end", ">=", self.scheduled_date_end),
                    ("person_ids", "in", person.id),
                ]
            fsm_orders = self.env["fsm.order"].search(domain) - self
            if fsm_orders:
                for order in fsm_orders:
                    reserved_name_workers.append(
                        "* "
                        + person.name
                        + " is allocated on "
                        + order.name
                        + " - "
                        + order.location_id.name
                        + "\n",
                    )

        if reserved_name_workers:
            raise UserError(
                _(
                    "These worker(s) are already allocated in other FSM Orders in the same "
                    "period:\n\n %s" % ("".join(reserved_name_workers))
                )
            )
