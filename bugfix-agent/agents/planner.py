from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.planner_parsing import coerce_content_to_text, parse_structured_json
from agents.schemas import StructuredPlan
from config import settings
from tools.pageindex_search import semantic_search


def _build_llm():
    if settings.llm_provider == "ollama":
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(model=settings.ollama_model, base_url=settings.ollama_base_url)

    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model=settings.gemini_model, temperature=0)


class PlannerAgent:
    def __init__(self) -> None:
        self.llm = _build_llm()

    def plan(self, bug_description: str) -> dict[str, Any]:
        index_hits = semantic_search(bug_description)
        sys = SystemMessage(
            content=(
                "You are a planner agent. Return strictly JSON matching keys: "
                "bug_summary, root_cause, files_to_modify, patches, tests_to_add, bash_commands."
            )
        )
        human = HumanMessage(
            content=f"Bug: {bug_description}\nSearch results: {json.dumps(index_hits, indent=2)}"
        )
        response = self.llm.invoke([sys, human])
        raw = coerce_content_to_text(response.content)
        data = parse_structured_json(raw)
        plan = StructuredPlan.model_validate(data)
        return {"ok": True, "plan": plan.model_dump()}

