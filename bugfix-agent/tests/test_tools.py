from pathlib import Path

from tools.ast_editor import edit_file
from tools.bash_tool import bash
from tools.dependency import graph
from tools.file_tools import read_file, write_file
from tools.pageindex_search import pageindex, semantic_search


def test_file_tools_roundtrip(tmp_path: Path):
    p = tmp_path / "x.py"
    write = write_file(str(p), "value = 1\n")
    assert write["ok"]
    read = read_file(str(p))
    assert read["content"] == "value = 1\n"


def test_ast_edit_generates_diff(tmp_path: Path):
    p = tmp_path / "mod.py"
    p.write_text("def foo():\n    return 1\n", encoding="utf-8")
    result = edit_file(
        str(p),
        {"type": "rewrite_function", "function_name": "foo", "new_body": "return 2"},
    )
    assert result["ok"]
    assert "--- a/" in result["diff"]


def test_bash_requires_approval():
    denied = bash("echo hi", prompt_fn=lambda _: "no")
    assert denied["status"] == "denied"


def test_pageindex_and_dependency(tmp_path: Path):
    file_a = tmp_path / "a.py"
    file_b = tmp_path / "b.py"
    file_a.write_text("from b import hello\n\ndef call():\n    return hello()\n", encoding="utf-8")
    file_b.write_text("def hello():\n    return 'ok'\n", encoding="utf-8")

    pageindex.build(str(tmp_path))
    search = semantic_search("hello")
    assert search["ok"]
    assert search["results"]

    graph.build(str(tmp_path))
    dependents = graph.get_dependents("b.py")
    assert "a.py" in dependents
