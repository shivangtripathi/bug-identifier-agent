from agents.planner_parsing import coerce_content_to_text, parse_structured_json


def test_coerce_content_to_text_from_message_blocks():
    content = [
        {"type": "text", "text": "```json"},
        {"type": "text", "text": '{"bug_summary":"x"}'},
        {"type": "text", "text": "```"},
    ]

    assert coerce_content_to_text(content) == "```json\n{\"bug_summary\":\"x\"}\n```"


def test_parse_structured_json_extracts_object_from_text_wrapping():
    raw = (
        "Here is the plan:\n"
        "```json\n"
        "{\"bug_summary\":\"Fix validation\",\"root_cause\":\"LLM returned list\","
        "\"files_to_modify\":[],\"patches\":[],\"tests_to_add\":[],\"bash_commands\":[]}\n"
        "```"
    )

    data = parse_structured_json(raw)

    assert data["bug_summary"] == "Fix validation"
    assert data["root_cause"] == "LLM returned list"


def test_parse_structured_json_handles_list_payload_by_picking_first_object():
    raw = '[{"bug_summary":"Fix", "root_cause":"x"}]'

    data = parse_structured_json(raw)

    assert data == {"bug_summary": "Fix", "root_cause": "x"}
