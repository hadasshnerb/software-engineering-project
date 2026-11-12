"""Baseline maximum-cardinality matching without relaxations."""

from collections import deque

from src.models import AllocationInstance


class BaselineMatcher:
    """Find a maximum matching using only originally compatible edges."""

    def solve(self, instance: AllocationInstance) -> dict[str, str]:
        adjacency = {agent: [] for agent in instance.agents}
        for agent, resource in instance.compatible_edges:
            adjacency[agent].append(resource)

        agent_match: dict[str, str | None] = {
            agent: None for agent in instance.agents
        }
        resource_match: dict[str, str] = {}

        while True:
            distances: dict[str, int] = {}
            queue: deque[str] = deque()
            for agent in instance.agents:
                if agent_match[agent] is None:
                    distances[agent] = 0
                    queue.append(agent)

            shortest_path: int | None = None
            while queue:
                agent = queue.popleft()
                if shortest_path is not None and distances[agent] >= shortest_path:
                    continue
                for resource in adjacency[agent]:
                    matched_agent = resource_match.get(resource)
                    if matched_agent is None:
                        shortest_path = distances[agent] + 1
                    elif matched_agent not in distances:
                        distances[matched_agent] = distances[agent] + 1
                        queue.append(matched_agent)

            if shortest_path is None:
                break

            def augment(agent: str) -> bool:
                for resource in adjacency[agent]:
                    matched_agent = resource_match.get(resource)
                    if matched_agent is None:
                        if distances[agent] + 1 != shortest_path:
                            continue
                    elif (
                        distances.get(matched_agent) != distances[agent] + 1
                        or not augment(matched_agent)
                    ):
                        continue

                    agent_match[agent] = resource
                    resource_match[resource] = agent
                    return True

                distances.pop(agent, None)
                return False

            for agent in instance.agents:
                if agent_match[agent] is None:
                    augment(agent)

        return {
            agent: resource
            for agent, resource in agent_match.items()
            if resource is not None
        }
