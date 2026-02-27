from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PatchInstruction(BaseModel):
    file_path: str
    function_name: str | None = None
    change_type: Literal["insert", "update", "delete"]
    rationale: str
    new_code: str = ""


class TestInstruction(BaseModel):
    file_path: str
    test_name: str
    content: str


class StructuredPlan(BaseModel):
    bug_summary: str
    root_cause: str
    files_to_modify: list[str] = Field(default_factory=list)
    patches: list[PatchInstruction] = Field(default_factory=list)
    tests_to_add: list[TestInstruction] = Field(default_factory=list)
    bash_commands: list[str] = Field(default_factory=list)
