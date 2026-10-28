from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

FeedbackPolicy = Literal["legacy_all", "layered_v1"]
TERMINAL_STATUSES = {
    "verified",
    "failed",
    "budget_exhausted",
    "invalid_task",
    "stalled",
    "needs_review",
}


class Limits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_turns: int = Field(default=12, ge=1, le=30)
    max_tool_calls: int = Field(default=40, ge=1, le=100)
    max_output_tokens: int = Field(default=1800, ge=128, le=4096)
    max_observed_tokens: int = Field(default=60000, ge=1000, le=200000)
    max_context_chars: int = Field(default=65000, ge=4000, le=150000)
    max_seconds: int = Field(default=240, ge=10, le=900)
    max_repeated_test_states: int = Field(default=3, ge=2, le=10)


class RunState(BaseModel):
    run_id: str
    case_id: str
    provider: Literal["replay", "deepseek"]
    strategy: Literal["feedback", "single_patch"] = "feedback"
    # Old saved runs retain their original semantics when this field is absent.
    feedback_policy: FeedbackPolicy = "legacy_all"
    runner_kind: Literal["local", "docker"] = "local"
    runner_image: str = "python:3.12-slim"
    execution_image_id: str | None = None
    experiment_id: str | None = None
    repeat_index: int | None = None
    status: str = "created"
    model: str = ""
    created_at: str
    updated_at: str
    limits: Limits = Field(default_factory=Limits)
    turns: int = 0
    tool_calls: int = 0
    messages: list[dict[str, Any]] = Field(default_factory=list)
    pending_calls: list[dict[str, Any]] = Field(default_factory=list)
    usage: list[dict[str, Any]] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    baseline: dict[str, Any] | None = None
    final_public: dict[str, Any] | None = None
    grade: dict[str, Any] | None = None
    result_summary: str = ""
    error_code: str | None = None
    manifest: dict[str, str] = Field(default_factory=dict)
    patch_sha256: str | None = None
    case_sha256: str = ""
    tested_states: dict[str, int] = Field(default_factory=dict)
    checkpoints: list[str] = Field(default_factory=list)
    stop_reason: str | None = None

    @property
    def observed_tokens(self) -> int:
        return sum(item.get("total_tokens") or 0 for item in self.usage)
