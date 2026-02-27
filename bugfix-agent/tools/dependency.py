from __future__ import annotations

import ast
import importlib
import importlib.util
from pathlib import Path
from typing import Any

HAS_NETWORKX = importlib.util.find_spec("networkx") is not None
if HAS_NETWORKX:
    nx = importlib.import_module("networkx")


class DependencyGraph:
    def __init__(self) -> None:
        self.edges: dict[str, set[str]] = {}
        self.reverse: dict[str, set[str]] = {}
        self.graph = nx.DiGraph() if HAS_NETWORKX else None

    def build(self, repo_root: str) -> dict[str, Any]:
        root = Path(repo_root)
        self.edges.clear()
        self.reverse.clear()
        if HAS_NETWORKX and self.graph is not None:
            self.graph.clear()

        for path in root.rglob("*.py"):
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            rel = str(path.relative_to(root))
            self.edges.setdefault(rel, set())
            self.reverse.setdefault(rel, set())
            if HAS_NETWORKX and self.graph is not None:
                self.graph.add_node(rel)
            text = path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                target = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = f"{alias.name.replace('.', '/')}.py"
                        self._add_edge(rel, target)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    target = f"{node.module.replace('.', '/')}.py"
                    self._add_edge(rel, target)

        edge_count = sum(len(v) for v in self.edges.values())
        return {"ok": True, "nodes": len(self.edges), "edges": edge_count}

    def _add_edge(self, source: str, target: str) -> None:
        self.edges.setdefault(source, set()).add(target)
        self.reverse.setdefault(target, set()).add(source)
        if HAS_NETWORKX and self.graph is not None:
            self.graph.add_edge(source, target)

    def get_dependents(self, file_path: str) -> list[str]:
        if HAS_NETWORKX and self.graph is not None and file_path in self.graph:
            return sorted(nx.ancestors(self.graph, file_path))

        seen: set[str] = set()
        stack = list(self.reverse.get(file_path, set()))
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(self.reverse.get(node, set()))
        return sorted(seen)


graph = DependencyGraph()


def dependency_impact(file_path: str) -> dict[str, Any]:
    dependents = graph.get_dependents(file_path)
    return {"ok": True, "file_path": file_path, "dependents": dependents}
