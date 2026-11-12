"""Object-oriented experiment orchestration."""

from dataclasses import dataclass
from pathlib import Path

from src.algorithms import Algorithm1Matcher, BaselineMatcher
from src.data_loader import CourseDataLoader
from src.models import AllocationInstance
from src.validator import MatchingValidator


@dataclass(frozen=True)
class BaselineResult:
    assignments: tuple[tuple[str, str], ...]
    unassigned_agents: tuple[str, ...]

    @property
    def assignment_count(self) -> int:
        return len(self.assignments)


class BaselineExperimentRunner:
    """Load an instance, run Baseline, validate it, and summarize the result."""

    def __init__(
        self,
        data_loader: CourseDataLoader | None = None,
        matcher: BaselineMatcher | None = None,
        validator: MatchingValidator | None = None,
    ) -> None:
        self._data_loader = data_loader or CourseDataLoader()
        self._matcher = matcher or BaselineMatcher()
        self._validator = validator or MatchingValidator()

    def run(
        self,
        courses_path: str | Path,
        rooms_path: str | Path,
    ) -> BaselineResult:
        instance = self._data_loader.load(courses_path, rooms_path)
        return self.run_instance(instance)

    def run_instance(self, instance: AllocationInstance) -> BaselineResult:
        matching = self._matcher.solve(instance)
        self._validator.validate_baseline(instance, matching)
        assignments = tuple(sorted(matching.items()))
        unassigned_agents = tuple(
            agent for agent in instance.agents if agent not in matching
        )
        return BaselineResult(assignments, unassigned_agents)


@dataclass(frozen=True)
class Algorithm1Result:
    assignments: tuple[tuple[str, str], ...]
    unassigned_agents: tuple[str, ...]
    recommendations: tuple[tuple[str, str], ...]
    relaxation_cost: float
    budget: float
    budget_mode: str

    @property
    def assignment_count(self) -> int:
        return len(self.assignments)


class Algorithm1ExperimentRunner:
    """Run and validate the paper-inspired SNH-SB matching algorithm."""

    def __init__(
        self,
        matcher: Algorithm1Matcher | None = None,
        validator: MatchingValidator | None = None,
    ) -> None:
        self._matcher = matcher or Algorithm1Matcher()
        self._validator = validator or MatchingValidator()

    def run_instance(
        self,
        instance: AllocationInstance,
        budget: float,
        budget_mode: str = "size",
    ) -> Algorithm1Result:
        solution = self._matcher.solve(instance, budget, budget_mode)
        self._validator.validate_algorithm1(
            instance,
            solution.assignments,
            solution.recommendations,
            budget,
            budget_mode,
        )
        assignments = tuple(sorted(solution.assignments.items()))
        unassigned_agents = tuple(
            agent for agent in instance.agents if agent not in solution.assignments
        )
        costs = {
            (edge.agent_id, edge.resource_id): edge.relaxation_cost
            for edge in instance.relaxable_edges
        }
        relaxation_cost = sum(
            costs[pair] for pair in solution.recommendations
            if costs[pair] is not None
        )
        return Algorithm1Result(
            assignments,
            unassigned_agents,
            solution.recommendations,
            relaxation_cost,
            budget,
            budget_mode,
        )