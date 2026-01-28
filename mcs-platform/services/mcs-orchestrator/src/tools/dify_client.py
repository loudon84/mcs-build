"""Dify client for chatflow calls."""

import json
from typing import Any, Optional

import httpx

from mcs_contracts import ErrorInfo
from observability.metrics import dify_calls_total
from observability.retry import retry_with_backoff
from settings import Settings


class DifyClient:
    """Client for Dify chatflow API."""

    def __init__(self, base_url: str, app_key: str, timeout: int = 120, retries: int = 3):
        """Initialize Dify client."""
        self.base_url = base_url.rstrip("/")
        self.app_key = app_key
        self.timeout = timeout
        self.retries = retries

    async def chatflow_async(
        self,
        query: str,
        user: str,
        inputs: dict[str, Any],
        files: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Call Dify chatflow asynchronously."""
        url = f"{self.base_url}/v1/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.app_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": inputs,
            "query": query,
            "user": user,
            "response_mode": "blocking",
        }

        if files:
            payload["files"] = files

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await self._call_with_retry(client, url, headers, payload)
                result = response.json()

                # Parse answer
                answer = result.get("answer", "")
                answer_json = self._parse_json_answer(answer)

                if answer_json.get("ok", False):
                    dify_calls_total.labels(app_key=self.app_key[:10], status="success").inc()
                else:
                    dify_calls_total.labels(app_key=self.app_key[:10], status="failed").inc()

                return answer_json

        except Exception as e:
            dify_calls_total.labels(app_key=self.app_key[:10], status="error").inc()
            return {
                "ok": False,
                "reason": f"Dify API call failed: {str(e)}",
                "raw_answer": None,
            }

    @retry_with_backoff(max_retries=3, retry_on=(httpx.HTTPError, httpx.TimeoutException))
    async def _call_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict,
        payload: dict,
    ) -> httpx.Response:
        """Call Dify API with retry."""
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 429:
            # Rate limit, retry
            raise httpx.HTTPStatusError("Rate limited", request=response.request, response=response)
        response.raise_for_status()
        return response

    def chatflow_blocking(
        self,
        query: str,
        user: str,
        inputs: dict[str, Any],
        files: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Call Dify chatflow synchronously (wrapper around async)."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.chatflow_async(query, user, inputs, files))

    def _parse_json_answer(self, answer: str) -> dict[str, Any]:
        """Parse JSON answer from Dify, with fallback."""
        # Try to parse as JSON
        try:
            # Try direct JSON parse
            return json.loads(answer)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in answer:
                start = answer.find("```json") + 7
                end = answer.find("```", start)
                if end > start:
                    try:
                        return json.loads(answer[start:end].strip())
                    except json.JSONDecodeError:
                        pass

            # Try to extract JSON object
            start = answer.find("{")
            end = answer.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(answer[start:end])
                except json.JSONDecodeError:
                    pass

            # Failed to parse, return error
            return {
                "ok": False,
                "reason": "Failed to parse JSON from Dify answer",
                "raw_answer": answer,
            }

