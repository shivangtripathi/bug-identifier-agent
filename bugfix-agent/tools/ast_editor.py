from __future__ import annotations

import difflib
import importlib
import importlib.util
from pathlib import Path
from typing import Any

HAS_LIBCST = importlib.util.find_spec("libcst") is not None
if HAS_LIBCST:
    cst = importlib.import_module("libcst")


def _fallback_rewrite(before: str, function_name: str, new_body: str) -> tuple[bool, str]:
    lines = before.splitlines()
    target = f"def {function_name}("
    for idx, line in enumerate(lines):
        if line.lstrip().startswith(target):
            indent = " " * (len(line) - len(line.lstrip()) + 4)
            body_lines = [f"{indent}{segment}" for segment in new_body.splitlines() if segment.strip()]
            if not body_lines:
                body_lines = [f"{indent}pass"]
            end = idx + 1
            while end < len(lines) and (lines[end].startswith(indent) or not lines[end].strip()):
                end += 1
            updated = lines[: idx + 1] + body_lines + lines[end:]
            return True, "\n".join(updated) + "\n"
    return False, before


def edit_file(file_path: str, ast_transform: dict[str, Any]) -> dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        return {"ok": False, "error": "file_not_found", "file_path": file_path}

    before = path.read_text(encoding="utf-8")
    transform_type = ast_transform.get("type")
    if transform_type != "rewrite_function":
        return {"ok": False, "error": "unsupported_transform", "transform": ast_transform}

    function_name = ast_transform["function_name"]
    new_body = ast_transform["new_body"]

    if HAS_LIBCST:
        class FunctionRewriter(cst.CSTTransformer):
            def __init__(self, function_name: str, new_body: str) -> None:
                self.function_name = function_name
                self.replaced = False
                body_module = cst.parse_module(new_body)
                self.new_statements = body_module.body

            def leave_FunctionDef(self, original_node, updated_node):
                if original_node.name.value != self.function_name:
                    return updated_node
                self.replaced = True
                indented = cst.IndentedBlock(body=self.new_statements)
                return updated_node.with_changes(body=indented)

        module = cst.parse_module(before)
        rewriter = FunctionRewriter(function_name=function_name, new_body=new_body)
        after = module.visit(rewriter).code
        replaced = rewriter.replaced
    else:
        replaced, after = _fallback_rewrite(before, function_name, new_body)

    if not replaced:
        return {
            "ok": False,
            "error": "function_not_found",
            "file_path": file_path,
            "function_name": function_name,
        }

    diff = "\n".join(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        )
    )
    return {
        "ok": True,
        "file_path": file_path,
        "function_name": function_name,
        "change_type": "update",
        "diff": diff,
        "updated_content": after,
        "engine": "libcst" if HAS_LIBCST else "fallback",
    }
