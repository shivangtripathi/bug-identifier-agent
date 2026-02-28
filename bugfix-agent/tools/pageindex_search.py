from __future__ import annotations

import ast
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import chromadb
except ModuleNotFoundError:  # pragma: no cover - fallback for restricted test environments
    chromadb = None


@dataclass(slots=True)
class Chunk:
    file_path: str
    start_line: int
    end_line: int
    symbol: str
    content: str


class _DeterministicEmbeddingFunction:
    """Deterministic local embedding to avoid external model downloads."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def name(self) -> str:
        return "deterministic-hash"

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:2], "big") % self.dimensions
            vector[bucket] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm:
            return [value / norm for value in vector]
        return vector


class _InMemoryCollection:
    def __init__(self, embedding_function: _DeterministicEmbeddingFunction) -> None:
        self.embedding_function = embedding_function
        self._rows: dict[str, tuple[str, dict[str, Any], list[float]]] = {}

    def count(self) -> int:
        return len(self._rows)

    def get(self, include: list[str] | None = None) -> dict[str, Any]:
        return {"ids": list(self._rows)}

    def delete(self, ids: list[str]) -> None:
        for row_id in ids:
            self._rows.pop(row_id, None)

    def add(self, ids: list[str], documents: list[str], metadatas: list[dict[str, Any]]) -> None:
        embeds = self.embedding_function(documents)
        for row_id, doc, metadata, embed in zip(ids, documents, metadatas, embeds):
            self._rows[row_id] = (doc, metadata, embed)

    def query(self, query_texts: list[str], n_results: int) -> dict[str, Any]:
        query_embed = self.embedding_function(query_texts)[0]
        scored: list[tuple[float, dict[str, Any]]] = []
        for doc, metadata, doc_embed in self._rows.values():
            distance = self._cosine_distance(query_embed, doc_embed)
            scored.append((distance, metadata))
        scored.sort(key=lambda item: item[0])
        top = scored[:n_results]
        return {
            "metadatas": [[metadata for _, metadata in top]],
            "distances": [[distance for distance, _ in top]],
        }

    @staticmethod
    def _cosine_distance(a: list[float], b: list[float]) -> float:
        dot = sum(i * j for i, j in zip(a, b))
        return 1.0 - dot


class _InMemoryChromaClient:
    def __init__(self) -> None:
        self._collections: dict[str, _InMemoryCollection] = {}

    def get_or_create_collection(
        self, name: str, embedding_function: _DeterministicEmbeddingFunction
    ) -> _InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = _InMemoryCollection(embedding_function)
        return self._collections[name]


class PageIndexEngine:
    """Semantic index backed by ChromaDB with symbol-aware Python chunks."""

    def __init__(self) -> None:
        self.embedding_fn = _DeterministicEmbeddingFunction()
        self.client = chromadb.Client() if chromadb is not None else _InMemoryChromaClient()
        self.collection = self.client.get_or_create_collection(
            name="code_chunks", embedding_function=self.embedding_fn
        )

    def build(self, repo_root: str) -> dict[str, Any]:
        root = Path(repo_root)
        files_indexed = 0
        chunks: list[Chunk] = []

        for path in root.rglob("*.py"):
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            chunks.extend(self._chunk_file(path, text, root))
            files_indexed += 1

        if self.collection.count():
            existing = self.collection.get(include=[])
            if existing.get("ids"):
                self.collection.delete(ids=existing["ids"])

        if chunks:
            ids = [f"{chunk.file_path}:{chunk.start_line}:{chunk.end_line}" for chunk in chunks]
            docs = [f"{chunk.symbol}\n{chunk.content}" for chunk in chunks]
            metadatas = [
                {
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "symbol": chunk.symbol,
                }
                for chunk in chunks
            ]
            self.collection.add(ids=ids, documents=docs, metadatas=metadatas)

        return {"ok": True, "files_indexed": files_indexed, "chunks": len(chunks)}

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
        if not self.collection.count():
            return {"ok": True, "query": query, "results": []}

        hits = self.collection.query(query_texts=[query], n_results=top_k)
        metadatas = hits.get("metadatas", [[]])[0]
        distances = hits.get("distances", [[]])[0]

        results = []
        for metadata, distance in zip(metadatas, distances):
            score = 1.0 / (1.0 + float(distance))
            results.append(
                {
                    "file_path": metadata["file_path"],
                    "line_range": [metadata["start_line"], metadata["end_line"]],
                    "symbol": metadata["symbol"],
                    "score": round(score, 4),
                }
            )
        return {"ok": True, "query": query, "results": results}


pageindex = PageIndexEngine()


def semantic_search(query: str) -> dict[str, Any]:
    return pageindex.query(query)
