"""Graph registry for managing multiple business graphs."""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from pydantic import BaseModel


@dataclass
class GraphInfo:
    """Graph information."""

    name: str
    version: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    build_callable: Callable[..., Any]  # Returns Runnable/Graph
    required_scopes: list[str] = None  # For gateway permission mapping

    def __post_init__(self):
        """Initialize default values."""
        if self.required_scopes is None:
            self.required_scopes = []


class GraphRegistry:
    """Registry for managing graphs."""

    def __init__(self):
        """Initialize graph registry."""
        self._graphs: dict[str, dict[str, GraphInfo]] = {}  # {name: {version: GraphInfo}}

    def register(self, graph_info: GraphInfo) -> None:
        """Register a graph."""
        if graph_info.name not in self._graphs:
            self._graphs[graph_info.name] = {}
        self._graphs[graph_info.name][graph_info.version] = graph_info

    def get(self, name: str, version: Optional[str] = None) -> Optional[GraphInfo]:
        """Get a graph by name and optional version."""
        if name not in self._graphs:
            return None

        versions = self._graphs[name]
        if version:
            return versions.get(version)
        else:
            # Return latest version
            if versions:
                return max(versions.values(), key=lambda g: g.version)
            return None

    def list_graphs(self) -> list[GraphInfo]:
        """List all registered graphs."""
        graphs = []
        for versions in self._graphs.values():
            graphs.extend(versions.values())
        return graphs

