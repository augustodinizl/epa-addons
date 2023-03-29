from odoo.exceptions import UserError
from odoo.tests import common


class TestFsmOrder(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.FsmOrder = self.env["fsm.order"]

        self.person1 = self.env.ref("fieldservice.person_1")
        self.person2 = self.env.ref("fieldservice.person_2")

        self.location1 = self.env.ref("fieldservice.test_location")

        # Create fsm.order records for testing
        self.fsm_order1 = self.FsmOrder.create(
            {
                "name": "FSM Order 1",
                "location_id": self.location1.id,
                "person_ids": [(6, 0, [self.person1.id])],
                "scheduled_date_start": "2023-03-20 10:00:00",
                "scheduled_date_end": "2023-03-20 14:00:00",
            }
        )

    def test_onchange_person_ids(self):
        # Test if an error is raised when the person is already allocated in the same period
        fsm_order2 = self.FsmOrder.new(
            {
                "name": "FSM Order 2",
                "location_id": self.location1.id,
                "person_ids": [(6, 0, [self.person1.id])],
                "scheduled_date_start": "2023-03-20 12:00:00",
                "scheduled_duration": 4,
            }
        )

        with self.assertRaises(UserError):
            fsm_order2._onchange_person_ids()

        # Test if no error is raised when the person is not allocated in the same period
        fsm_order3 = self.FsmOrder.new(
            {
                "name": "FSM Order 3",
                "location_id": self.location1.id,
                "person_ids": [(6, 0, [self.person2.id])],
                "scheduled_date_start": "2023-03-20 12:00:00",
                "scheduled_duration": 4,
            }
        )

        self.assertIsNone(fsm_order3._onchange_person_ids())

    def test_compute_scheduled_days_duration(self):
        self.assertEqual(self.fsm_order1.scheduled_days_duration, 4 / 24)

    def test_onchange_scheduled_days_duration(self):
        self.fsm_order1.scheduled_days_duration = 2
        self.fsm_order1.onchange_scheduled_days_duration()
        self.assertEqual(self.fsm_order1.scheduled_duration, 2 * 24)

    def test_onchange_duration_time(self):
        self.fsm_order1.scheduled_duration = 48
        self.fsm_order1.onchange_duration_time()
        self.assertEqual(self.fsm_order1.scheduled_days_duration, 48 / 24)
