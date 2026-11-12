"""Run one or more allocation algorithms on the same CSV instance."""

import argparse
import json
from math import isfinite
from pathlib import Path

from src.data_loader import CourseDataLoader
from src.experiments import Algorithm1ExperimentRunner, BaselineExperimentRunner


class AllocationCommand:
    """Command-line entry point for running the allocation algorithms."""

    def run(self, arguments: list[str] | None = None) -> int:
        parser = argparse.ArgumentParser(
            description="Run course-to-classroom allocation algorithms"
        )
        parser.add_argument(
            "--algorithm",
            choices=("baseline", "algorithm1", "all"),
            default="all",
            help="Algorithm to run (default: all)",
        )
        parser.add_argument(
            "--budget",
            type=float,
            default=None,
            help="Algorithm 1 relaxation budget (size or discomfort units)",
        )
        parser.add_argument(
            "--budget-mode",
            choices=("size", "discomfort"),
            default="size",
            help="Budget aggregation for Algorithm 1 (default: size)",
        )
        parser.add_argument(
            "--courses",
            type=Path,
            default=Path("data/example/courses.csv"),
            help="Path to courses.csv",
        )
        parser.add_argument(
            "--rooms",
            type=Path,
            default=Path("data/example/rooms.csv"),
            help="Path to rooms.csv",
        )
        options = parser.parse_args(arguments)

        instance = CourseDataLoader().load(options.courses, options.rooms)
        budget = (
            (
                float(min(len(instance.agents), len(instance.resources)))
                if options.budget_mode == "size"
                else sum(
                    float(edge.relaxation_cost)
                    for edge in instance.relaxable_edges
                )
            )
            if options.budget is None
            else options.budget
        )
        if not isfinite(budget) or budget < 0:
            parser.error("--budget must be non-negative")
        if options.budget_mode == "size" and not float(budget).is_integer():
            parser.error("--budget must be an integer when --budget-mode=size")

        results = []
        if options.algorithm in {"baseline", "all"}:
            result = BaselineExperimentRunner().run_instance(instance)
            results.append(
                {
                    "algorithm": "baseline",
                    "assignment_count": result.assignment_count,
                    "assignments": [
                        {"request_id": agent, "room_and_time_slot": resource}
                        for agent, resource in result.assignments
                    ],
                    "unassigned_requests": list(result.unassigned_agents),
                }
            )

        if options.algorithm in {"algorithm1", "all"}:
            result = Algorithm1ExperimentRunner().run_instance(
                instance, budget, options.budget_mode
            )
            results.append(
                {
                    "algorithm": "algorithm1_snh_sb",
                    "relaxation_budget": budget,
                    "budget_mode": options.budget_mode,
                    "assignment_count": result.assignment_count,
                    "assignments": [
                        {"request_id": agent, "room_and_time_slot": resource}
                        for agent, resource in result.assignments
                    ],
                    "unassigned_requests": list(result.unassigned_agents),
                    "recommendations": [
                        {"request_id": agent, "room_and_time_slot": resource}
                        for agent, resource in result.recommendations
                    ],
                    "recommendation_cost": result.relaxation_cost,
                }
            )

        print(json.dumps({"results": results}, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(AllocationCommand().run())
