from __future__ import annotations

from pathlib import Path
from typing import Any


def read_file(file_path: str) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        return {"ok": False, "error": "file_not_found", "file_path": file_path}
    content = path.read_text(encoding="utf-8")
    return {"ok": True, "file_path": file_path, "content": content}


def write_file(file_path: str, content: str) -> dict[str, Any]:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {
        "ok": True,
        "file_path": file_path,
        "bytes_written": len(content.encode("utf-8")),
    }
