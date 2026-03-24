"""Plan structures used by the scaffolded multi-agent flow."""

from typing import Literal

from backend.core.base_model import MasonBaseModel


class PlanStep(MasonBaseModel):
    step_id: str
    description: str
    status: Literal["pending", "in_progress", "completed"] = "pending"


class PlanSpec(MasonBaseModel):
    trace_id: str
    goal: str
    steps: list[PlanStep]

