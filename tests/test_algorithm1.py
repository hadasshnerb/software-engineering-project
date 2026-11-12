import itertools
import unittest

import networkx as nx

from src.algorithms import Algorithm1Matcher
from src.experiments import Algorithm1ExperimentRunner
from src.models import AllocationEdge, AllocationInstance


class Algorithm1MatcherTests(unittest.TestCase):
    def setUp(self):
        self.matcher = Algorithm1Matcher()

    def test_selects_lower_cost_recommendation(self):
        instance = AllocationInstance(
            agents=("c1",),
            resources=("r1", "r2"),
            edges=(
                AllocationEdge("c1", "r1", "relaxable", 1.0),
                AllocationEdge("c1", "r2", "relaxable", 2.0),
            ),
        )

        solution = self.matcher.solve(
            instance, budget=1, budget_mode="discomfort"
        )

        self.assertEqual(solution.recommendations, (("c1", "r1"),))
        self.assertEqual(solution.assignments, {"c1": "r1"})

    def test_zero_budget_does_not_recommend_relaxations(self):
        instance = AllocationInstance(
            agents=("c1",),
            resources=("r1",),
            edges=(AllocationEdge("c1", "r1", "relaxable", 1.0),),
        )

        solution = self.matcher.solve(instance, budget=0)

        self.assertEqual(solution.recommendations, ())
        self.assertEqual(solution.assignments, {})

    def test_recommendation_increases_matching_without_harming_guaranteed_agents(self):
        instance = AllocationInstance(
            agents=("c1", "c2", "c3"),
            resources=("r1", "r2", "r3"),
            edges=(
                AllocationEdge("c1", "r1", "compatible"),
                AllocationEdge("c2", "r1", "compatible"),
                AllocationEdge("c2", "r2", "compatible"),
                AllocationEdge("c3", "r3", "relaxable", 1.0),
            ),
        )

        solution = self.matcher.solve(instance, budget=1)

        self.assertEqual(len(solution.assignments), 3)
        self.assertEqual(solution.recommendations, (("c3", "r3"),))

    def test_rejects_negative_budget(self):
        instance = AllocationInstance(agents=(), resources=(), edges=())

        with self.assertRaisesRegex(ValueError, "non-negative"):
            self.matcher.solve(instance, budget=-1)

    def test_size_budget_must_be_an_integer(self):
        instance = AllocationInstance(agents=(), resources=(), edges=())

        with self.assertRaisesRegex(ValueError, "must be an integer"):
            self.matcher.solve(instance, budget=0.5)

    def test_recommendations_satisfy_snh_sb_on_all_two_by_three_graphs(self):
        agents = ("c1", "c2")
        resources = ("r1", "r2", "r3")
        pairs = tuple(itertools.product(agents, resources))

        for statuses in itertools.product(range(3), repeat=len(pairs)):
            edges = tuple(
                AllocationEdge(agent, resource, "compatible")
                if status == 1
                else AllocationEdge(
                    agent, resource, "relaxable", 1.0 + index % 2
                )
                for index, ((agent, resource), status) in enumerate(zip(pairs, statuses))
                if status
            )
            instance = AllocationInstance(agents, resources, edges)
            for budget_mode, budgets in (
                ("size", range(min(len(agents), len(resources)) + 1)),
                ("discomfort", range(5)),
            ):
                for budget in budgets:
                    solution = self.matcher.solve(
                        instance, budget, budget_mode=budget_mode
                    )
                    budget_used = (
                        len(solution.recommendations)
                        if budget_mode == "size"
                        else sum(
                            edge.relaxation_cost
                            for edge in instance.relaxable_edges
                            if (edge.agent_id, edge.resource_id)
                            in solution.recommendations
                        )
                    )
                    self.assertLessEqual(budget_used, budget)
                    base_guaranteed = _guaranteed_agents(
                        agents, resources, set(instance.compatible_edges)
                    )

                    for count in range(len(solution.recommendations) + 1):
                        for subset in itertools.combinations(
                            solution.recommendations, count
                        ):
                            graph_edges = set(instance.compatible_edges) | set(subset)
                            guaranteed = _guaranteed_agents(
                                agents, resources, graph_edges
                            )
                            relaxers = {agent for agent, _ in subset}
                            self.assertTrue(base_guaranteed <= guaranteed)
                            self.assertTrue(relaxers <= guaranteed)

    def test_runner_reports_recommendations_and_cost(self):
        instance = AllocationInstance(
            agents=("c1",),
            resources=("r1",),
            edges=(AllocationEdge("c1", "r1", "relaxable", 2.0),),
        )

        result = Algorithm1ExperimentRunner().run_instance(instance, budget=1)

        self.assertEqual(result.assignment_count, 1)
        self.assertEqual(result.recommendations, (("c1", "r1"),))
        self.assertEqual(result.relaxation_cost, 2.0)


def _guaranteed_agents(agents, resources, edges):
    graph = nx.Graph()
    graph.add_nodes_from(agents, bipartite=0)
    graph.add_nodes_from(resources, bipartite=1)
    graph.add_edges_from(edges)
    matching = nx.bipartite.maximum_matching(graph, top_nodes=set(agents))
    maximum_size = sum(agent in matching for agent in agents)

    guaranteed = set()
    for agent in agents:
        reduced_graph = graph.copy()
        reduced_graph.remove_node(agent)
        reduced_agents = set(agents) - {agent}
        reduced_matching = nx.bipartite.maximum_matching(
            reduced_graph, top_nodes=reduced_agents
        )
        reduced_size = sum(item in reduced_matching for item in reduced_agents)
        if reduced_size < maximum_size:
            guaranteed.add(agent)
    return guaranteed


if __name__ == "__main__":
    unittest.main()
