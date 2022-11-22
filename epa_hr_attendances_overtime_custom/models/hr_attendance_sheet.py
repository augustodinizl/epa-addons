# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from pytz import timezone

from odoo import api, models


class HrAttendanceSheet(models.Model):

    _inherit = "hr.attendance.sheet"

    @api.multi
    def get_attendance(self, data):
        """Get Attendance History Of Employee."""
        attendance_ids = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("check_in", ">=", self.request_date_from),
                ("check_in", "<=", self.request_date_to),
            ]
        )
        lst = []
        vals = {}
        dates = [
            self.request_date_from + timedelta(days=x)
            for x in range((self.request_date_to - self.request_date_from).days + 1)
        ]
        self.attendance_sheet_ids.unlink()

        for date in dates:
            vals = {}
            if date not in lst:
                lst.append(date)
                vals = self._calc_current_attendance(attendance_ids, date)
                vals.update({"name_id": self.id, "date": date})
                vals.update({"status": "weekday"})

                if vals["psignin"] == 0.0 and vals["psignout"] == 0.0:
                    vals.update({"status": "weekend"})

                if vals["psignin"] and vals["psignout"]:
                    if vals["asignin"] == 0.0 and vals["asignout"] == 0.0:
                        resource_id = self.employee_id.resource_id
                        leave = (
                            self.employee_id.resource_calendar_id.leave_ids.filtered(
                                lambda l: (
                                    not l.resource_id or l.resource_id == resource_id
                                )
                                and timezone("UTC")
                                .localize(l.date_from)
                                .astimezone(timezone(resource_id.tz))
                                .date()
                                <= date
                                and timezone("UTC")
                                .localize(l.date_to)
                                .astimezone(timezone(resource_id.tz))
                                .date()
                                >= date
                            )
                        )

                        if leave:
                            vals.update({"status": "leave"})
                        if not leave:
                            vals.update({"status": "absence"})

                if vals["asignin"] > vals["psignin"] and vals["status"] == "weekday":
                    late = vals["asignin"] - vals["psignin"]
                    vals.update({"latein": late})

                avg_hours = (
                    self.employee_id
                    and self.employee_id.resource_calendar_id
                    and self.employee_id.resource_calendar_id.hours_per_day
                    or False
                )

                resource_calendar_id = (
                    self.employee_id and self.employee_id.resource_calendar_id
                )

                for line in resource_calendar_id.attendance_ids:
                    if line.date_from == date or line.date_to == date:
                        avg_hours = line.hour_to - line.hour_from

                if vals["total_attendance"] > avg_hours:
                    vals.update(
                        {"overtime": vals["total_attendance"] - avg_hours or False}
                    )

                if vals["status"] == "weekend" and vals["total_attendance"]:
                    vals.update({"overtime": vals["total_attendance"] or False})

                if (
                    vals["total_attendance"] < avg_hours
                    and vals["psignin"] > 0.0
                    and vals["psignout"] > 0.0
                ):
                    if vals.get("status") == "weekday":
                        vals.update(
                            {"difftime": avg_hours - vals["total_attendance"] or False}
                        )
                flage = True
                if vals["status"] == "weekend" and vals.get("overtime", False) <= 0.0:
                    continue
                if vals["status"] == "absence":
                    for line in resource_calendar_id.attendance_ids:

                        if (
                            int(date.weekday()) == int(line.dayofweek)
                            and line.date_from
                            and line.date_to
                        ):
                            if not line.date_to == date or line.date_from == date:
                                vals = {}

                if flage and vals:
                    self.env["hr.attendance.sheet.line"].create(vals)
        self.employee_id.attendance_sheet_id = self.id or False
