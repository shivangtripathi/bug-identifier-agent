from __future__ import annotations

from typing import Any

from tools.ast_editor import edit_file
from tools.bash_tool import bash
from tools.dependency import dependency_impact
from tools.file_tools import read_file, write_file


class ExecutorAgent:
    def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        results: dict[str, Any] = {
            "reads": [],
            "patches": [],
            "writes": [],
            "dependency": [],
            "bash": [],
        }

        for file_path in plan.get("files_to_modify", []):
            results["reads"].append(read_file(file_path))
            results["dependency"].append(dependency_impact(file_path))

        for patch in plan.get("patches", []):
            transform = {
                "type": "rewrite_function",
                "function_name": patch.get("function_name"),
                "new_body": patch.get("new_code", "pass"),
            }
            patched = edit_file(patch["file_path"], transform)
            results["patches"].append(patched)
            if patched.get("ok"):
                results["writes"].append(
                    write_file(patch["file_path"], patched["updated_content"])
                )

        for test_item in plan.get("tests_to_add", []):
            results["writes"].append(write_file(test_item["file_path"], test_item["content"]))

        for command in plan.get("bash_commands", []):
            results["bash"].append(bash(command))

        return {"ok": True, "results": results}
