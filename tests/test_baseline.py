import tempfile
import unittest
from pathlib import Path

from src.algorithms import BaselineMatcher
from src.data_loader import CourseDataLoader
from src.experiments import BaselineExperimentRunner
from src.models import AllocationEdge, AllocationInstance
from src.validator import MatchingValidator


class BaselineMatcherTests(unittest.TestCase):
    def setUp(self):
        self.matcher = BaselineMatcher()

    def test_finds_maximum_matching_by_rerouting_an_existing_match(self):
        instance = AllocationInstance(
            agents=("c1", "c2"),
            resources=("r1", "r2"),
            edges=(
                AllocationEdge("c1", "r1", "compatible"),
                AllocationEdge("c1", "r2", "compatible"),
                AllocationEdge("c2", "r1", "compatible"),
            ),
        )

        matching = self.matcher.solve(instance)

        self.assertEqual(len(matching), 2)
        self.assertEqual(set(matching), {"c1", "c2"})
        self.assertEqual(set(matching.values()), {"r1", "r2"})

    def test_ignores_relaxable_edges_and_their_costs(self):
        instance = AllocationInstance(
            agents=("c1", "c2"),
            resources=("r1", "r2"),
            edges=(
                AllocationEdge("c1", "r1", "compatible"),
                AllocationEdge("c2", "r2", "relaxable", 0.0),
            ),
        )

        self.assertEqual(self.matcher.solve(instance), {"c1": "r1"})

    def test_returns_empty_matching_without_compatible_edges(self):
        instance = AllocationInstance(agents=("c1",), resources=("r1",), edges=())

        self.assertEqual(self.matcher.solve(instance), {})


class CourseDataLoaderTests(unittest.TestCase):
    def test_loads_example_csv_files(self):
        root = Path(__file__).resolve().parents[1]
        instance = CourseDataLoader().load(
            root / "data/example/courses.csv",
            root / "data/example/rooms.csv",
        )

        self.assertEqual(len(instance.agents), 4)
        self.assertEqual(len(instance.resources), 4)
        self.assertEqual(len(instance.compatible_edges), 4)
        self.assertEqual(len(instance.relaxable_edges), 4)
        self.assertEqual(len(instance.meetings), 4)
        self.assertEqual(len(instance.classrooms), 2)
        self.assertEqual(instance.meetings[0].planned_registered_students, 40)
        self.assertEqual(instance.classrooms[0].capacity, 40)
        self.assertEqual(instance.relaxable_edges[0].relaxation_cost, 1)

    def test_capacity_edges_follow_paper_preference_bands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "courses.csv").write_text(
                "group_id,planned_registered_students,period,weekday,"
                "start_time,end_time\n"
                "g1,53,Sem_A,Tuesday,14:00,16:00\n",
                encoding="utf-8",
            )
            (root / "rooms.csv").write_text(
                "classrooms_eng_id,Capacity\n"
                "below,49\n"
                "minimum,50\n"
                "maximum,79\n"
                "above,80\n",
                encoding="utf-8",
            )

            instance = CourseDataLoader().load(
                root / "courses.csv",
                root / "rooms.csv",
            )

        edges = {edge.resource_id.split("@")[0]: edge for edge in instance.edges}
        self.assertEqual(edges["below"].status, "relaxable")
        self.assertEqual(edges["below"].relaxation_cost, 1)
        self.assertEqual(edges["minimum"].status, "compatible")
        self.assertEqual(edges["maximum"].status, "compatible")
        self.assertEqual(edges["above"].status, "relaxable")
        self.assertEqual(edges["above"].relaxation_cost, 1)

    def test_room_resource_is_shared_by_meetings_in_the_same_exact_slot(self):
        root = Path(__file__).resolve().parents[1]
        instance = CourseDataLoader().load(
            root / "data/example/courses.csv",
            root / "data/example/rooms.csv",
        )

        same_slot_resource = "r1@Sem_A|Tuesday|14:00-16:00"
        matched_requests = {
            request_id
            for request_id, resource_id in instance.compatible_edges
            if resource_id == same_slot_resource
        }
        self.assertEqual(matched_requests, {"g1:1", "g2"})

    def test_rejects_room_capacity_that_is_not_an_integer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "courses.csv").write_text(
                "group_id,code,planned_registered_students,"
                "period,weekday,start_time,end_time\n"
                "g1,CS101,30,Sem_A,Tuesday,14:00,16:00\n",
                encoding="utf-8",
            )
            (root / "rooms.csv").write_text(
                "classrooms_eng_id,Capacity\n"
                "r1,large\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "Expected an integer for Capacity"):
                CourseDataLoader().load(
                    root / "courses.csv",
                    root / "rooms.csv",
                )


class MatchingValidatorTests(unittest.TestCase):
    def test_rejects_non_compatible_baseline_assignment(self):
        instance = AllocationInstance(
            agents=("c1",),
            resources=("r1",),
            edges=(AllocationEdge("c1", "r1", "relaxable", 1.0),),
        )

        with self.assertRaisesRegex(ValueError, "non-compatible edge"):
            MatchingValidator().validate_baseline(instance, {"c1": "r1"})


class BaselineExperimentRunnerTests(unittest.TestCase):
    def test_runs_and_reports_assignments_and_unassigned_agents(self):
        instance = AllocationInstance(
            agents=("c1", "c2", "c3"),
            resources=("r1", "r2"),
            edges=(
                AllocationEdge("c1", "r1", "compatible"),
                AllocationEdge("c1", "r2", "compatible"),
                AllocationEdge("c2", "r1", "compatible"),
            ),
        )

        result = BaselineExperimentRunner().run_instance(instance)

        self.assertEqual(result.assignment_count, 2)
        self.assertEqual(result.unassigned_agents, ("c3",))


if __name__ == "__main__":
    unittest.main()
