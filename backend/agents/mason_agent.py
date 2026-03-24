"""High-level agent facade for future complex orchestration."""

from __future__ import annotations

from backend.agents.base_agent import BaseAgent
from backend.agents.multi_agent.executor import ExecutorAgent
from backend.agents.multi_agent.planner import PlannerAgent
from backend.agents.multi_agent.reporter import ReporterAgent


class MasonAgent(BaseAgent):
    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.reporter = ReporterAgent()

    def run(self, question: str, user_role: str = "normal") -> dict:
        plan = self.planner.plan(question)
        evidence = self.executor.run(question, user_role)
        report = self.reporter.report(question, evidence)
        return {"plan": plan, "evidence": evidence, "report": report}

