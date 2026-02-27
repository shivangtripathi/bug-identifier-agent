from __future__ import annotations

import json
from typing import Any


def coerce_content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_blocks = [block.get("text", "") for block in content if isinstance(block, dict)]
        merged_text = "\n".join(text for text in text_blocks if text)
        if merged_text:
            return merged_text
    return json.dumps(content)


def parse_structured_json(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for idx, ch in enumerate(raw):
        if ch not in "[{":
            continue
        try:
            candidate, _ = decoder.raw_decode(raw[idx:])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            return candidate
        if isinstance(candidate, list) and candidate and isinstance(candidate[0], dict):
            return candidate[0]

    raise ValueError("Planner output did not include a valid JSON object")
