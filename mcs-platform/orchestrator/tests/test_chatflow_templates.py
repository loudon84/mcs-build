"""Tests for Chatflow JSON template tools."""

import pytest

from tools.chatflow_templates import (
    build_agent_payload,
    build_chatflow_payload,
    get_agent_app_template,
    get_chatflow_app_template,
)


def test_build_chatflow_payload_returns_dict_with_required_keys():
    """build_chatflow_payload returns a dict with inputs, query, user, response_mode."""
    payload = build_chatflow_payload(
        query="test query",
        user="user@example.com",
        inputs={"key": "value"},
    )
    assert isinstance(payload, dict)
    assert payload["query"] == "test query"
    assert payload["user"] == "user@example.com"
    assert payload["inputs"] == {"key": "value"}
    assert payload["response_mode"] == "blocking"
    assert "files" not in payload


def test_build_chatflow_payload_includes_files_when_provided():
    """build_chatflow_payload includes files key when files is non-empty."""
    files = [{"type": "file", "transfer_method": "remote_url", "url": "https://example.com/f"}]
    payload = build_chatflow_payload(
        query="q",
        user="u",
        inputs={},
        files=files,
    )
    assert "files" in payload
    assert payload["files"] == files


def test_build_chatflow_payload_returns_new_dict_not_shared_reference():
    """build_chatflow_payload returns a new dict; mutating it does not affect inputs."""
    inputs = {"a": 1}
    payload = build_chatflow_payload(query="q", user="u", inputs=inputs)
    payload["inputs"]["b"] = 2
    assert "b" not in inputs
    assert payload["inputs"] is not inputs


def test_build_agent_payload_same_structure_as_chatflow():
    """build_agent_payload returns the same structure as build_chatflow_payload."""
    payload = build_agent_payload(
        query="agent query",
        user="agent_user",
        inputs={"x": "y"},
    )
    assert payload["query"] == "agent query"
    assert payload["user"] == "agent_user"
    assert payload["inputs"] == {"x": "y"}
    assert payload["response_mode"] == "blocking"


def test_get_chatflow_app_template_returns_dict_with_expected_keys():
    """get_chatflow_app_template returns dict with app_type, name, description, nodes, edges, variables."""
    t = get_chatflow_app_template(name="My Chatflow", description="A test chatflow")
    assert isinstance(t, dict)
    assert t["app_type"] == "chatflow"
    assert t["name"] == "My Chatflow"
    assert t["description"] == "A test chatflow"
    assert t["nodes"] == []
    assert t["edges"] == []
    assert t["variables"] == []


def test_get_agent_app_template_returns_dict_with_app_type_agent():
    """get_agent_app_template returns dict with app_type agent."""
    t = get_agent_app_template(name="My Agent", description="A test agent")
    assert t["app_type"] == "agent"
    assert t["name"] == "My Agent"
    assert t["description"] == "A test agent"
    assert t["nodes"] == []
    assert t["edges"] == []
    assert t["variables"] == []


def test_app_templates_return_new_list_instances():
    """get_*_app_template returns new lists for nodes/edges/variables; mutating does not affect other calls."""
    t1 = get_chatflow_app_template(name="A")
    t2 = get_chatflow_app_template(name="B")
    t1["nodes"].append("node1")
    assert len(t2["nodes"]) == 0
    assert t1["nodes"] is not t2["nodes"]
