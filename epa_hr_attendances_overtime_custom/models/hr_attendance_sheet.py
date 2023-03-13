# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, time, timedelta

import pytz
from pytz import timezone

from odoo import api, fields, models


class HrAttendanceSheet(models.Model):

    _inherit = "hr.attendance.sheet"

    total_attendance = fields.Float("Total Attendance")
    total_planned_attendance = fields.Float("Total Planned Attendance")
    attendance_ids = fields.One2many(
        "hr.attendance", string="HR Attendance", compute="_compute_attendances"
    )

    def _compute_attendances(self):
        for line in self:
            line.attendance_ids = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", line.employee_id.id),
                    ("check_in", ">=", line.request_date_from),
                    ("check_in", "<=", line.request_date_to),
                ],
                order="check_in",
            )

    # EPA Refactor
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
                    # if vals["asignin"] == 0.0 and vals["asignout"] == 0.0:
                    resource_id = self.employee_id.resource_id
                    leave = self.employee_id.resource_calendar_id.leave_ids.filtered(
                        lambda l: (not l.resource_id or l.resource_id == resource_id)
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

                    if leave:
                        vals.update({"status": "leave"})
                    if not leave and vals["asignin"] == 0.0 and vals["asignout"] == 0.0:
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

                # Calcula corretamente o tempo planejado
                tz = self.employee_id.resource_id.calendar_id.tz
                if vals["status"] in ["weekday", "absence", "leave"]:
                    vals.update(
                        {
                            "total_planned_attendance": self.employee_id.with_context(
                                exclude_public_holidays=True,
                                employee_id=self.employee_id.id,
                            ).get_work_days_data(
                                datetime.combine(
                                    date, time(0, 0, 0, 0, tzinfo=pytz.timezone(tz))
                                ),
                                datetime.combine(
                                    date,
                                    time(23, 59, 59, 99999, tzinfo=pytz.timezone(tz)),
                                ),
                                # Pass this domain for excluding leaves whose type is
                                # included in theoretical hours
                                domain=[
                                    "|",
                                    ("holiday_id", "=", False),
                                    (
                                        "holiday_id.holiday_status_id.include_in_theoretical",
                                        "=",
                                        False,
                                    ),
                                ],
                            )[
                                "hours"
                            ]
                        }
                    )

                if flage and vals:
                    self.env["hr.attendance.sheet.line"].create(vals)
        self.employee_id.attendance_sheet_id = self.id or False

    @api.multi
    def compute_attendance_data(self):
        super().compute_attendance_data()
        for rec in self:
            total_attendance = 0
            total_planned_attendance = 0
            for line in rec.attendance_sheet_ids:
                total_attendance = total_attendance + line.total_attendance
                total_planned_attendance = (
                    total_planned_attendance + line.total_planned_attendance
                )
            rec.total_attendance = total_attendance
            rec.total_planned_attendance = total_planned_attendance
            total_absence = rec.total_planned_attendance - rec.total_attendance
            if total_absence >= 0:
                rec.total_absense = total_absence

    @api.multi
    def print_document(self):
        self.ensure_one()
        [data] = self.read()
        datas = {"ids": [], "model": "hr.attendance.sheet", "form": data}
        return self.env.ref(
            "epa_hr_attendances_overtime_custom.action_report_hr_attendance_sheet"
        ).report_action(self, data=datas)


class HrAttendanceSheetLine(models.Model):
    """Attendance Sheet Line."""

    _inherit = "hr.attendance.sheet.line"

    total_planned_attendance = fields.Float(string="Total Planned Attendance")
