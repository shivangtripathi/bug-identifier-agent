from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Chunk:
    file_path: str
    start_line: int
    end_line: int
    symbol: str
    content: str


class PageIndexEngine:
    """A lightweight PageIndex-style semantic index with symbol-aware chunks."""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []

    def build(self, repo_root: str) -> dict[str, Any]:
        root = Path(repo_root)
        files_indexed = 0
        self.chunks.clear()

        for path in root.rglob("*.py"):
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            self.chunks.extend(self._chunk_file(path, text, root))
            files_indexed += 1

        return {"ok": True, "files_indexed": files_indexed, "chunks": len(self.chunks)}

    def _chunk_file(self, path: Path, text: str, root: Path) -> list[Chunk]:
        rel = str(path.relative_to(root))
        lines = text.splitlines()
        chunks: list[Chunk] = []
        tree = ast.parse(text)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = node.lineno
                end = getattr(node, "end_lineno", start)
                symbol = node.name
                content = "\n".join(lines[start - 1 : end])
                chunks.append(Chunk(rel, start, end, symbol, content))
        if not chunks:
            chunks.append(Chunk(rel, 1, len(lines), "<module>", text))
        return chunks

    def query(self, query: str, top_k: int = 5) -> dict[str, Any]:
        terms = [t for t in re.split(r"\W+", query.lower()) if t]
        scored = []
        for chunk in self.chunks:
            haystack = f"{chunk.symbol.lower()}\n{chunk.content.lower()}"
            score = sum(haystack.count(term) for term in terms)
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        results = [
            {
                "file_path": chunk.file_path,
                "line_range": [chunk.start_line, chunk.end_line],
                "symbol": chunk.symbol,
                "score": score,
            }
            for score, chunk in scored[:top_k]
        ]
        return {"ok": True, "query": query, "results": results}


pageindex = PageIndexEngine()


def semantic_search(query: str) -> dict[str, Any]:
    return pageindex.query(query)
