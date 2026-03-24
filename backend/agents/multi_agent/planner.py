"""Planning agent scaffold."""

from __future__ import annotations

from uuid import uuid4

from backend.search.tool.deeper_research import DeeperResearchTool


class PlannerAgent:
    def __init__(self) -> None:
        self.tool = DeeperResearchTool()

    def plan(self, question: str):
        return self.tool.build_plan(uuid4().hex, question)

