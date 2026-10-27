from __future__ import annotations

import json
import time
from typing import Protocol

import httpx

from .config import Settings


class ProviderError(RuntimeError):
    """Only safe codes, never provider bodies or authenticated request objects."""


class Provider(Protocol):
    model: str

    def complete(self, messages: list[dict], tools: list[dict], max_tokens: int) -> dict: ...


class DeepSeekProvider:
    def __init__(self, settings: Settings, transport=None):
        if not settings.api_key:
            raise ProviderError("missing_deepseek_api_key")
        self.settings = settings
        self.model = settings.model
        self.client = httpx.Client(
            base_url=settings.base_url + "/",
            timeout=settings.request_timeout,
            headers={"Authorization": f"Bearer {settings.api_key}"},
            transport=transport,
        )

    def close(self):
        self.client.close()

    def _request(self, method: str, route: str, body=None) -> dict:
        try:
            response = self.client.request(method, route, json=body)
            if response.status_code != 200:
                raise ProviderError(f"provider_http_{response.status_code}")
            return response.json()
        except ProviderError:
            raise
        except httpx.TimeoutException:
            raise ProviderError("provider_timeout") from None
        except (httpx.HTTPError, ValueError):
            raise ProviderError("provider_transport_or_json_error") from None

    def discover(self) -> list[str]:
        response = self._request("GET", "models")
        models = [
            item["id"]
            for item in response.get("data", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        if not self.model:
            self.model = next(
                (name for name in ("deepseek-flash", "deepseek-chat") if name in models), ""
            )
            if not self.model:
                raise ProviderError("set_deepseek_model_to_a_supported_model")
        if self.model not in models:
            raise ProviderError("configured_model_not_in_provider_catalog")
        return models

    def complete(self, messages: list[dict], tools: list[dict], max_tokens: int) -> dict:
        if not self.model:
            self.discover()
        started = time.monotonic()
        body = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "max_tokens": max_tokens,
            "stream": False,
            "thinking": {"type": "disabled"},
            "temperature": 0,
        }
        response = self._request("POST", "chat/completions", body)
        try:
            choice = response["choices"][0]
            message = choice["message"]
            if message.get("role") != "assistant":
                raise ProviderError("provider_invalid_assistant_message")
            content = message.get("content")
            if content is not None and not isinstance(content, str):
                raise ProviderError("provider_invalid_message_content")
            clean = {"role": "assistant", "content": content}
            if message.get("tool_calls"):
                if not isinstance(message["tool_calls"], list):
                    raise ProviderError("provider_invalid_tool_calls")
                clean["tool_calls"] = message["tool_calls"]
            return {
                "message": clean,
                "usage": response.get("usage", {}),
                "finish_reason": choice.get("finish_reason"),
                "elapsed_seconds": round(time.monotonic() - started, 3),
            }
        except (KeyError, IndexError, TypeError):
            raise ProviderError("provider_invalid_response_schema") from None


class ReplayProvider:
    model = "scripted-replay-not-a-model"

    def __init__(self, case: dict):
        self.case = case

    def complete(self, messages: list[dict], tools: list[dict], max_tokens: int) -> dict:
        turn = sum(message["role"] == "assistant" for message in messages)
        steps = [
            [("list_files", {})],
            [
                ("read_file", {"path": path})
                for path in self.case["files"]
                if path.startswith("project/") and path.endswith(".py")
            ],
            [("run_tests", {})],
            [("replace_text", edit) for edit in self.case["replay_edits"]],
            [("run_tests", {})],
        ]
        if turn < len(steps):
            calls = [
                {
                    "id": f"replay_{turn}_{index}",
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": json.dumps(args, ensure_ascii=False),
                    },
                }
                for index, (name, args) in enumerate(steps[turn])
            ]
            message = {"role": "assistant", "content": None, "tool_calls": calls}
        else:
            message = {"role": "assistant", "content": "固定脚本回放完成。请查看独立评分。"}
        return {"message": message, "usage": {}, "finish_reason": "stop", "elapsed_seconds": 0}
