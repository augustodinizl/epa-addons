# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FsmOrder(models.Model):
    _inherit = "fsm.order"

    scheduled_days_duration = fields.Float(
        string="Scheduled days duration",
        help="Scheduled duration of the work in days",
        compute="_compute_scheduled_days_duration",
        readonly=False,
    )

    team_coordinator_id = fields.Many2one(
        "fsm.person", string="Team Coordinator", index=True
    )

    def _compute_scheduled_days_duration(self):
        self.scheduled_days_duration = self.scheduled_duration / 24

    @api.onchange("scheduled_days_duration")
    def onchange_scheduled_days_duration(self):
        if self.scheduled_days_duration and self.scheduled_date_start:
            self.scheduled_duration = self.scheduled_days_duration * 24

    @api.onchange("scheduled_date_start", "scheduled_duration")
    def onchange_scheduled_duration(self):
        super().onchange_scheduled_duration()
        self.scheduled_days_duration = self.scheduled_duration / 24

    # TODO: se for o caso muda para um onchange
    @api.depends("person_ids", "person_id")
    def _compute_person_reservation(self):
        def get_reserved_name_workers(person_ids):
            reserved_name_workers = []

            for person in person_ids:
                fsm_orders = self.env["fsm.order"].search(get_domain(person))
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
            return reserved_name_workers

        def get_domain(person):
            fsm_order_id = self.id
            if not isinstance(fsm_order_id, int):
                fsm_order_id = self._origin.id
            common_domain = [
                ("id", "!=", fsm_order_id),
                ("date_end", "=", None),
                "|",
                ("person_ids", "in", person.id),
                ("person_id", "=", person.id),
            ]

            if not self.scheduled_date_end:
                date_domain = [
                    ("scheduled_date_start", "<=", self.scheduled_date_start),
                    ("scheduled_date_end", ">=", self.scheduled_date_start),
                ]
            else:
                date_domain = [
                    ("scheduled_date_start", "<=", self.scheduled_date_end),
                    ("scheduled_date_end", ">=", self.scheduled_date_end),
                ]
            return common_domain + date_domain

        if self.scheduled_date_start:
            person_ids = self.person_ids + self.person_id
            reserved_name_workers = get_reserved_name_workers(person_ids)

            if reserved_name_workers:
                raise UserError(
                    _(
                        "These worker(s) are already allocated in other FSM Orders in the same "
                        "period:\n\n %s" % ("".join(reserved_name_workers))
                    )
                )
        else:
            self.schedule_date_end = False

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        self._compute_person_reservation()
        return res
