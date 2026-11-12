"""CSV input loading for allocation instances."""

import csv
import re
from collections import Counter
from pathlib import Path

from src.models import (
    AllocationEdge,
    AllocationInstance,
    Classroom,
    CourseMeeting,
)


class CourseDataLoader:
    """Load course meetings and classrooms in the paper's tabular format."""

    def load(
        self,
        courses_path: str | Path,
        rooms_path: str | Path,
    ) -> AllocationInstance:
        meeting_rows = self._read_rows(
            courses_path,
            {
                "group_id",
                "planned_registered_students",
                "period",
                "weekday",
                "start_time",
                "end_time",
            },
        )
        room_rows = self._read_rows(
            rooms_path,
            {
                "classrooms_eng_id",
                "Capacity",
            },
        )

        group_counts = Counter(
            self._required_value(row, "group_id") for row in meeting_rows
        )
        group_occurrences: Counter[str] = Counter()
        meetings_list = []
        for line_number, row in enumerate(meeting_rows, start=2):
            group_id = self._required_value(row, "group_id")
            meeting_id = self._optional_value(row, "meeting_id")
            if not meeting_id and group_counts[group_id] > 1:
                group_occurrences[group_id] += 1
                meeting_id = str(group_occurrences[group_id])
            meetings_list.append(
                self._parse_meeting(row, line_number, meeting_id)
            )
        meetings = tuple(meetings_list)
        rooms = tuple(
            self._parse_classroom(row, line_number)
            for line_number, row in enumerate(room_rows, start=2)
        )
        self._validate_unique_ids(
            (meeting.request_id for meeting in meetings), "request ID"
        )
        self._validate_unique_ids(
            (classroom.classroom_id for classroom in rooms), "classroom ID"
        )

        agents = tuple(meeting.request_id for meeting in meetings)
        time_slots = tuple(dict.fromkeys(meeting.time_slot_id for meeting in meetings))
        resources = tuple(
            f"{classroom.classroom_id}@{time_slot}"
            for time_slot in time_slots
            for classroom in rooms
        )
        edges = tuple(
            self._create_capacity_edge(meeting, classroom)
            for meeting in meetings
            for classroom in rooms
        )
        return AllocationInstance(agents, resources, edges, meetings, rooms)

    @staticmethod
    def _create_capacity_edge(
        meeting: CourseMeeting, classroom: Classroom
    ) -> AllocationEdge:
        student_count = meeting.planned_registered_students
        room_tier = classroom.capacity // 10
        minimum_tier = student_count // 10
        maximum_tier = min((4 * student_count) // 30, 27)
        cost = max(minimum_tier - room_tier, 0) + max(room_tier - maximum_tier, 0)

        return AllocationEdge(
            meeting.request_id,
            f"{classroom.classroom_id}@{meeting.time_slot_id}",
            "compatible" if cost == 0 else "relaxable",
            None if cost == 0 else float(cost),
        )

    @staticmethod
    def _read_rows(
        path: str | Path, required_columns: set[str]
    ) -> list[dict[str, str | None]]:
        csv_path = Path(path)
        with csv_path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise ValueError(f"CSV file has no header: {csv_path}")
            missing = required_columns - set(reader.fieldnames)
            if missing:
                raise ValueError(
                    f"{csv_path} is missing required columns: {', '.join(sorted(missing))}"
                )
            rows = []
            for line_number, row in enumerate(reader, start=2):
                if None in row:
                    raise ValueError(
                        f"{csv_path} has too many columns on line {line_number}"
                    )
                if any(value and value.strip() for value in row.values()):
                    rows.append(row)
            return rows

    @staticmethod
    def _required_value(row: dict[str, str | None], column: str) -> str:
        value = row.get(column)
        if value is None or not value.strip():
            raise ValueError(f"CSV row has an empty {column}")
        return value.strip()

    @classmethod
    def _parse_meeting(
        cls, row: dict[str, str | None], line_number: int, meeting_id: str
    ) -> CourseMeeting:
        group_id = cls._required_value(row, "group_id")
        start_time = cls._required_value(row, "start_time")
        end_time = cls._required_value(row, "end_time")
        cls._validate_time(start_time, line_number)
        cls._validate_time(end_time, line_number)
        if start_time >= end_time:
            raise ValueError(f"Start time must be before end time on line {line_number}")

        return CourseMeeting(
            group_id=group_id,
            meeting_id=meeting_id,
            code=cls._optional_value(row, "code"),
            course_name=cls._optional_value(row, "course_name"),
            credits=cls._optional_float(row, "credits", line_number),
            weekly_hours=cls._optional_float(row, "weekly_hours", line_number),
            planned_registered_students=cls._required_int(
                row, "planned_registered_students", line_number
            ),
            actual_enrollment=cls._optional_int(row, "actual_enrollment", line_number),
            waitlist=cls._optional_int(row, "waitlist", line_number),
            period=cls._required_value(row, "period"),
            weekday=cls._required_value(row, "weekday"),
            start_time=start_time,
            end_time=end_time,
            current_room=cls._optional_value(row, "current_room"),
            instructor=cls._optional_value(row, "instructor"),
            branch=cls._optional_value(row, "branch"),
        )

    @classmethod
    def _parse_classroom(
        cls, row: dict[str, str | None], line_number: int
    ) -> Classroom:
        raw_accessories = cls._optional_value(row, "Accessories")
        accessories = (
            ()
            if not raw_accessories or raw_accessories.upper() == "NULL"
            else tuple(item.strip() for item in raw_accessories.split(",") if item.strip())
        )
        return Classroom(
            classroom_id=cls._required_value(row, "classrooms_eng_id"),
            region=cls._optional_value(row, "Region"),
            building=cls._optional_value(row, "Building"),
            room=cls._optional_value(row, "Room"),
            capacity=cls._required_int(row, "Capacity", line_number),
            accessories=accessories,
        )

    @staticmethod
    def _optional_value(row: dict[str, str | None], column: str) -> str:
        value = row.get(column)
        if value is None:
            return ""
        normalized = value.strip()
        if normalized == "-" or normalized.upper() == "NULL" or not normalized:
            return ""
        return normalized

    @classmethod
    def _required_int(
        cls, row: dict[str, str | None], column: str, line_number: int
    ) -> int:
        value = cls._required_value(row, column)
        try:
            parsed = int(value)
        except ValueError as error:
            raise ValueError(
                f"Expected an integer for {column} on line {line_number}: {value!r}"
            ) from error
        if parsed < 0:
            raise ValueError(f"{column} must be non-negative on line {line_number}")
        return parsed

    @classmethod
    def _optional_int(
        cls, row: dict[str, str | None], column: str, line_number: int
    ) -> int:
        if not cls._optional_value(row, column):
            return 0
        return cls._required_int(row, column, line_number)

    @classmethod
    def _optional_float(
        cls, row: dict[str, str | None], column: str, line_number: int
    ) -> float:
        value = cls._optional_value(row, column)
        if not value:
            return 0.0
        try:
            parsed = float(value)
        except ValueError as error:
            raise ValueError(
                f"Expected a number for {column} on line {line_number}: {value!r}"
            ) from error
        if parsed < 0:
            raise ValueError(f"{column} must be non-negative on line {line_number}")
        return parsed

    @staticmethod
    def _validate_time(value: str, line_number: int) -> None:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            raise ValueError(
                f"Time must use HH:MM 24-hour format on line {line_number}: {value!r}"
            )

    @staticmethod
    def _validate_unique_ids(values, label: str) -> None:
        value_list = list(values)
        if len(set(value_list)) != len(value_list):
            raise ValueError(f"{label}s must be unique")