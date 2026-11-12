"""Domain models shared by the allocation algorithms."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal


EdgeStatus = Literal["compatible", "relaxable"]


@dataclass(frozen=True)
class AllocationEdge:
    agent_id: str
    resource_id: str
    status: EdgeStatus
    relaxation_cost: float | None = None

    def __post_init__(self) -> None:
        if self.status == "compatible":
            if self.relaxation_cost is not None:
                raise ValueError("Compatible edges must not have a relaxation cost")
        elif self.status == "relaxable":
            if self.relaxation_cost is None:
                raise ValueError("Relaxable edges must have a relaxation cost")
            if not isfinite(self.relaxation_cost) or self.relaxation_cost < 0:
                raise ValueError("Relaxation cost must be finite and non-negative")
        else:
            raise ValueError(f"Unsupported edge status: {self.status!r}")


@dataclass(frozen=True)
class AllocationInstance:
    agents: tuple[str, ...]
    resources: tuple[str, ...]
    edges: tuple[AllocationEdge, ...]
    meetings: tuple[CourseMeeting, ...] = ()
    classrooms: tuple[Classroom, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "agents", tuple(self.agents))
        object.__setattr__(self, "resources", tuple(self.resources))
        object.__setattr__(self, "edges", tuple(self.edges))
        object.__setattr__(self, "meetings", tuple(self.meetings))
        object.__setattr__(self, "classrooms", tuple(self.classrooms))

        if len(set(self.agents)) != len(self.agents):
            raise ValueError("Agent IDs must be unique")
        if len(set(self.resources)) != len(self.resources):
            raise ValueError("Resource IDs must be unique")
        if any(not identifier for identifier in (*self.agents, *self.resources)):
            raise ValueError("Agent and resource IDs must not be empty")

        agent_ids = set(self.agents)
        resource_ids = set(self.resources)
        edge_pairs: set[tuple[str, str]] = set()

        for edge in self.edges:
            if edge.agent_id not in agent_ids:
                raise ValueError(f"Edge refers to unknown agent: {edge.agent_id!r}")
            if edge.resource_id not in resource_ids:
                raise ValueError(
                    f"Edge refers to unknown resource: {edge.resource_id!r}"
                )
            pair = (edge.agent_id, edge.resource_id)
            if pair in edge_pairs:
                raise ValueError(f"Duplicate edge: {pair!r}")
            edge_pairs.add(pair)

    @property
    def compatible_edges(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (edge.agent_id, edge.resource_id)
            for edge in self.edges
            if edge.status == "compatible"
        )

    @property
    def relaxable_edges(self) -> tuple[AllocationEdge, ...]:
        return tuple(edge for edge in self.edges if edge.status == "relaxable")


@dataclass(frozen=True)
class CourseMeeting:
    group_id: str
    meeting_id: str
    code: str
    course_name: str
    credits: float
    weekly_hours: float
    planned_registered_students: int
    actual_enrollment: int
    waitlist: int
    period: str
    weekday: str
    start_time: str
    end_time: str
    current_room: str
    instructor: str
    branch: str

    @property
    def request_id(self) -> str:
        if not self.meeting_id:
            return self.group_id
        return f"{self.group_id}:{self.meeting_id}"

    @property
    def time_slot_id(self) -> str:
        return (
            f"{self.period}|{self.weekday}|"
            f"{self.start_time}-{self.end_time}"
        )


@dataclass(frozen=True)
class Classroom:
    classroom_id: str
    region: str
    building: str
    room: str
    capacity: int
    accessories: tuple[str, ...]
