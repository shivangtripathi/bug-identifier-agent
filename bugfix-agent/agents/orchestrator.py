from __future__ import annotations

from typing import Any, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langsmith import traceable

from agents.executor import ExecutorAgent
from agents.planner import PlannerAgent
from config import settings
from tools.dependency import graph
from tools.pageindex_search import pageindex


class ConversationState(TypedDict, total=False):
    bug_id: str
    conversation: list[str]
    conversation_summary: str
    active_bug: str
    plan: dict[str, Any]
    execution: dict[str, Any]


class Orchestrator:
    def __init__(self, repo_root: str) -> None:
        self.repo_root = repo_root
        pageindex.build(repo_root)
        graph.build(repo_root)
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.app = self._build_graph()

    def _compress(self, conversation: list[str]) -> tuple[list[str], str]:
        joined = "\n".join(conversation)
        if len(joined) <= settings.max_context_chars:
            return conversation, ""
        kept = conversation[-6:]
        summary = "Earlier context compressed: " + " | ".join(conversation[:-6])[-300:]
        return kept, summary

    @traceable(name="planner_step")
    def _plan_node(self, state: ConversationState) -> ConversationState:
        plan = self.planner.plan(state["active_bug"])
        return {"plan": plan["plan"]}

    @traceable(name="executor_step")
    def _execute_node(self, state: ConversationState) -> ConversationState:
        execution = self.executor.execute(state["plan"])
        return {"execution": execution}

    def _build_graph(self):
        flow = StateGraph(ConversationState)
        flow.add_node("plan", self._plan_node)
        flow.add_node("execute", self._execute_node)
        flow.add_edge(START, "plan")
        flow.add_edge("plan", "execute")
        flow.add_edge("execute", END)
        return flow.compile()

    def run_turn(self, conversation: list[str], bug_description: str) -> ConversationState:
        convo, summary = self._compress(conversation)
        state: ConversationState = {
            "bug_id": str(uuid4()),
            "conversation": convo,
            "conversation_summary": summary,
            "active_bug": bug_description,
        }
        return self.app.invoke(
            state,
            config={
                "tags": ["bugfix-agent", f"provider:{settings.llm_provider}", f"bug:{state['bug_id']}"]
            },
        )
