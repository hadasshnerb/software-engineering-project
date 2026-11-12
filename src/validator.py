"""Independent validation for allocation results."""

from math import isfinite

from src.models import AllocationInstance


class MatchingValidator:
    """Validate matching constraints and edge eligibility."""

    @staticmethod
    def _validate_matching(
        instance: AllocationInstance,
        matching: dict[str, str],
        allowed_edges: set[tuple[str, str]],
        edge_error_message: str = "Matching uses an edge not allowed by the algorithm",
    ) -> None:
        agent_ids = set(instance.agents)
        resource_ids = set(instance.resources)

        if len(matching.values()) != len(set(matching.values())):
            raise ValueError("A resource is assigned more than once")

        for agent, resource in matching.items():
            if agent not in agent_ids:
                raise ValueError(f"Matching contains unknown agent: {agent!r}")
            if resource not in resource_ids:
                raise ValueError(f"Matching contains unknown resource: {resource!r}")
            if (agent, resource) not in allowed_edges:
                raise ValueError(f"{edge_error_message}: ({agent!r}, {resource!r})")

    def validate_baseline(
        self, instance: AllocationInstance, matching: dict[str, str]
    ) -> None:
        self._validate_matching(
            instance,
            matching,
            set(instance.compatible_edges),
            "Baseline matching uses a non-compatible edge",
        )

    def validate_algorithm1(
        self,
        instance: AllocationInstance,
        matching: dict[str, str],
        recommendations: tuple[tuple[str, str], ...],
        budget: float,
        budget_mode: str = "size",
    ) -> None:
        if not isfinite(budget) or budget < 0:
            raise ValueError("Relaxation budget must be non-negative")
        if budget_mode not in {"size", "discomfort"}:
            raise ValueError(f"Unsupported relaxation budget mode: {budget_mode!r}")
        if budget_mode == "size" and not float(budget).is_integer():
            raise ValueError("A size budget must be an integer")

        relaxable_edges = {
            (edge.agent_id, edge.resource_id): edge.relaxation_cost
            for edge in instance.relaxable_edges
        }
        if len(set(recommendations)) != len(recommendations):
            raise ValueError("Algorithm 1 returned duplicate recommendations")
        if any(edge not in relaxable_edges for edge in recommendations):
            raise ValueError("Algorithm 1 recommended a non-relaxable edge")
        if len({agent for agent, _ in recommendations}) != len(recommendations):
            raise ValueError("Algorithm 1 recommended multiple relaxations for one agent")
        if len({resource for _, resource in recommendations}) != len(recommendations):
            raise ValueError("Algorithm 1 recommended a resource more than once")
        budget_used = (
            float(len(recommendations))
            if budget_mode == "size"
            else sum(
                cost
                for pair in recommendations
                if (cost := relaxable_edges[pair]) is not None
            )
        )
        if budget_used > budget:
            raise ValueError("Algorithm 1 exceeded its relaxation budget")
        self._validate_matching(
            instance,
            matching,
            set(instance.compatible_edges) | set(recommendations),
        )