"""Chatflow JSON template tools for Dify Agent and Chatflow."""

import copy
from typing import Any, Optional


def build_chatflow_payload(
    query: str,
    user: str,
    inputs: dict[str, Any],
    files: Optional[list[dict[str, Any]]] = None,
    response_mode: str = "blocking",
) -> dict[str, Any]:
    """Build Chatflow API request body for Dify /v1/chat-messages.

    Returns a new dict suitable for dify_client.chatflow_async; callers can
    mutate the returned dict without affecting shared state.

    Args:
        query: User query string.
        user: User identifier.
        inputs: Key/value pairs for workflow/chatflow variables.
        files: Optional list of file objects (e.g. type, transfer_method, url).
        response_mode: "blocking" or "streaming".

    Returns:
        Request body dict with keys: inputs, query, user, response_mode;
        includes "files" only when files is non-empty.
    """
    payload: dict[str, Any] = {
        "inputs": copy.deepcopy(inputs),
        "query": query,
        "user": user,
        "response_mode": response_mode,
    }
    if files:
        payload["files"] = copy.deepcopy(files)
    return payload


def build_agent_payload(
    query: str,
    user: str,
    inputs: dict[str, Any],
    files: Optional[list[dict[str, Any]]] = None,
    response_mode: str = "blocking",
) -> dict[str, Any]:
    """Build Agent API request body for Dify chat/agent API.

    Dify Agent uses the same chat-messages API as Chatflow; this returns
    the same structure as build_chatflow_payload.

    Args:
        query: User query string.
        user: User identifier.
        inputs: Key/value pairs for agent variables.
        files: Optional list of file objects.
        response_mode: "blocking" or "streaming".

    Returns:
        Request body dict compatible with Dify Agent/Chatflow API.
    """
    return build_chatflow_payload(
        query=query,
        user=user,
        inputs=inputs,
        files=files,
        response_mode=response_mode,
    )


def get_chatflow_app_template(
    name: str,
    description: str = "",
) -> dict[str, Any]:
    """Return a Chatflow app definition JSON skeleton for export/import.

    Structure aligns with common Dify workflow concepts (nodes, edges,
    variables). Keys may be adjusted when Dify export schema is available.

    Args:
        name: Application name.
        description: Optional description.

    Returns:
        New dict with app_type, name, description, nodes, edges, variables.
    """
    return {
        "app_type": "chatflow",
        "name": name,
        "description": description,
        "nodes": [],
        "edges": [],
        "variables": [],
    }


def get_agent_app_template(
    name: str,
    description: str = "",
) -> dict[str, Any]:
    """Return an Agent app definition JSON skeleton for export/import.

    Args:
        name: Application name.
        description: Optional description.

    Returns:
        New dict with app_type, name, description, nodes, edges, variables.
    """
    return {
        "app_type": "agent",
        "name": name,
        "description": description,
        "nodes": [],
        "edges": [],
        "variables": [],
    }
