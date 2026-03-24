"""Scaffold for deeper research workflows."""

from __future__ import annotations

from backend.core.plan_spec import PlanSpec, PlanStep


class DeeperResearchTool:
    """Produce a lightweight multi-step plan for complex questions."""

    def build_plan(self, trace_id: str, question: str) -> PlanSpec:
        steps = [
            PlanStep(step_id="collect", description="收集相关建材文档与制度证据"),
            PlanStep(step_id="analyze", description="对比施工工艺、标准条款与适用条件"),
            PlanStep(step_id="report", description="生成带证据链的内部答复"),
        ]
        return PlanSpec(trace_id=trace_id, goal=question, steps=steps)

