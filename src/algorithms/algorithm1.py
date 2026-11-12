"""Paper-inspired SNH-SB matching over the project's allocation model."""

from dataclasses import dataclass
from math import isfinite

import networkx as nx

from src.models import AllocationInstance


@dataclass(frozen=True)
class Algorithm1Solution:
    assignments: dict[str, str]
    recommendations: tuple[tuple[str, str], ...]


class Algorithm1Matcher:
    """Select SNH-SB relaxations using the paper's dummy-agent weighting."""

    def solve(
        self,
        instance: AllocationInstance,
        budget: float,
        budget_mode: str = "size",
    ) -> Algorithm1Solution:
        if not isfinite(budget) or budget < 0:
            raise ValueError("Relaxation budget must be non-negative")
        if budget_mode not in {"size", "discomfort"}:
            raise ValueError(f"Unsupported relaxation budget mode: {budget_mode!r}")
        if budget_mode == "size" and not float(budget).is_integer():
            raise ValueError("A size budget must be an integer")

        agents = set(instance.agents)
        resources = set(instance.resources)
        compatible = set(instance.compatible_edges)
        relaxable = {
            (edge.agent_id, edge.resource_id): float(edge.relaxation_cost)
            for edge in instance.relaxable_edges
        }

        graph = nx.Graph()
        graph.add_nodes_from(instance.agents, bipartite=0)
        graph.add_nodes_from(instance.resources, bipartite=1)

        original_weight = (len(instance.agents) + 1) ** 2
        for agent, resource in instance.compatible_edges:
            graph.add_edge(agent, resource, weight=original_weight)

        edge_penalties = {
            pair: 1.0 if budget_mode == "size" else cost
            for pair, cost in relaxable.items()
        }
        max_penalty = max(edge_penalties.values(), default=0.0)
        for (agent, resource), penalty in edge_penalties.items():
            normalized_penalty = penalty / max_penalty if max_penalty else 0.0
            graph.add_edge(
                agent,
                resource,
                weight=len(instance.agents) + 1 - normalized_penalty,
            )

        recommendations: tuple[tuple[str, str], ...] = ()
        max_dummies = len(instance.resources)

        for dummy_count in range(max_dummies + 1):
            weighted_graph = graph.copy()
            for index in range(dummy_count):
                dummy = ("paper-algorithm-dummy", index)
                weighted_graph.add_node(dummy, bipartite=0)
                for resource in instance.resources:
                    weighted_graph.add_edge(
                        dummy, resource, weight=len(instance.agents) + 1
                    )

            selected_matching = nx.max_weight_matching(
                weighted_graph, maxcardinality=False, weight="weight"
            )
            chosen = []
            for first, second in selected_matching:
                if first in agents and second in resources:
                    pair = (first, second)
                elif second in agents and first in resources:
                    pair = (second, first)
                else:
                    continue
                if pair in relaxable:
                    chosen.append(pair)

            budget_used = (
                float(len(chosen))
                if budget_mode == "size"
                else sum(relaxable[pair] for pair in chosen)
            )
            if budget_used <= budget:
                recommendations = tuple(sorted(chosen))
                break

        allowed_edges = compatible | set(recommendations)
        allocation_graph = nx.Graph()
        allocation_graph.add_nodes_from(instance.agents, bipartite=0)
        allocation_graph.add_nodes_from(instance.resources, bipartite=1)
        allocation_graph.add_edges_from(allowed_edges)
        matching = nx.bipartite.maximum_matching(
            allocation_graph, top_nodes=agents
        )
        assignments = {
            agent: matching[agent]
            for agent in instance.agents
            if agent in matching
        }
        return Algorithm1Solution(assignments, recommendations)
