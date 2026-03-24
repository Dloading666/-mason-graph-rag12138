"""Agent orchestration on top of multi-mode retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.config.prompts.qa_prompts import build_qa_system_prompt, build_qa_user_prompt
from backend.core.evidence import EvidenceItem
from backend.core.plan_spec import PlanSpec, PlanStep
from backend.graphrag_core.search.modes import MultiModeSearchService, RetrievalResult
from backend.graphrag_core.traces.store import TraceStore
from backend.llm.qwen_llm import QwenLLM


STANDARD_PATTERN = re.compile(r"(?:GB|JGJ)\s?\d+(?:\.\d+)?(?:-\d{4})?")


@dataclass
class AgentAnswer:
    """Structured agent output used by the API layer."""

    answer: str
    mode: str
    evidence: list[EvidenceItem]
    citations: list[str]
    trace_id: str
    plan: dict | None
    execution_summary: dict | None
    debug: dict | None


class BaseAgent:
    """Shared implementation for retrieval-grounded answering."""

    default_mode = "hybrid"

    def __init__(self) -> None:
        self.search = MultiModeSearchService()
        self.llm = QwenLLM()
        self.trace_store = TraceStore()

    def run(
        self,
        session: Session,
        *,
        question: str,
        user_role: str,
        requested_mode: str,
        need_evidence: bool,
        debug_enabled: bool,
    ) -> AgentAnswer:
        trace_id = uuid4().hex
        plan = self.build_plan(trace_id, question)
        retrieval = self.search.search(
            session,
            question=question,
            user_role=user_role,
            requested_mode=requested_mode or self.default_mode,
        )
        answer = self.generate_answer(question, retrieval)
        citations = self.collect_citations(answer, retrieval.evidence)
        execution_summary = {
            "retrieval_mode": retrieval.mode,
            "evidence_count": len(retrieval.evidence),
            "plan_steps": len(plan.steps) if plan else 0,
        }
        debug_payload = retrieval.debug if debug_enabled else None
        self.trace_store.record_trace(
            session,
            trace_id=trace_id,
            question=question,
            user_role=user_role,
            mode=retrieval.mode,
            answer=answer,
            plan=plan.model_dump(mode="json") if plan else None,
            execution_summary=execution_summary,
            debug=debug_payload,
            citations=citations,
        )
        return AgentAnswer(
            answer=answer,
            mode=retrieval.mode,
            evidence=retrieval.evidence if need_evidence else [],
            citations=citations,
            trace_id=trace_id,
            plan=plan.model_dump(mode="json") if plan else None,
            execution_summary=execution_summary,
            debug=debug_payload,
        )

    def build_plan(self, trace_id: str, question: str) -> PlanSpec | None:
        return PlanSpec(
            trace_id=trace_id,
            goal=question,
            steps=[
                PlanStep(step_id="retrieve", description="Collect graph and document evidence"),
                PlanStep(step_id="reason", description="Compare materials, processes, and standards"),
                PlanStep(step_id="respond", description="Return a grounded answer with citations"),
            ],
        )

    def generate_answer(self, question: str, retrieval: RetrievalResult) -> str:
        if not retrieval.evidence:
            return "当前知识库没有检索到足够证据，请补充相关建材文档后重试。"

        context_blocks = [f"[{item.citation}] {item.title}: {item.snippet}" for item in retrieval.evidence]
        messages = [
            {"role": "system", "content": build_qa_system_prompt()},
            {"role": "user", "content": build_qa_user_prompt(question, context_blocks)},
        ]
        generated = self.llm.safe_generate_chat_completion(messages)
        if generated:
            return generated

        bullets = "\n".join(f"{index}. {item.snippet}" for index, item in enumerate(retrieval.evidence, start=1))
        return f"基于知识库检索结果，关于“{question}”可参考以下要点：\n{bullets}"

    def collect_citations(self, answer: str, evidence: list[EvidenceItem]) -> list[str]:
        citations = set(STANDARD_PATTERN.findall(answer))
        for item in evidence:
            citations.update(STANDARD_PATTERN.findall(item.snippet))
            citations.add(item.citation)
        return sorted(citations)


class NaiveRagAgent(BaseAgent):
    default_mode = "naive"


class GraphAgent(BaseAgent):
    default_mode = "local"


class HybridAgent(BaseAgent):
    default_mode = "hybrid"


class DeepResearchAgent(BaseAgent):
    default_mode = "global"

    def build_plan(self, trace_id: str, question: str) -> PlanSpec | None:
        return PlanSpec(
            trace_id=trace_id,
            goal=question,
            steps=[
                PlanStep(step_id="decompose", description="Break the question into domain sub-topics"),
                PlanStep(step_id="collect", description="Collect local graph evidence and global community summaries"),
                PlanStep(step_id="synthesize", description="Write a concise internal research memo"),
            ],
        )

    def generate_answer(self, question: str, retrieval: RetrievalResult) -> str:
        if not retrieval.evidence:
            return super().generate_answer(question, retrieval)
        bullets = "\n".join(f"{index}. {item.snippet}" for index, item in enumerate(retrieval.evidence, start=1))
        return (
            f"问题：{question}\n"
            "结论：根据当前知识库，建议优先按下列证据执行。\n"
            f"依据：\n{bullets}\n"
            "建议：如涉及采购、施工或验收，请结合项目现场条件和现行标准复核。"
        )


class FusionGraphRAGAgent(BaseAgent):
    default_mode = "hybrid"

    def build_plan(self, trace_id: str, question: str) -> PlanSpec | None:
        return PlanSpec(
            trace_id=trace_id,
            goal=question,
            steps=[
                PlanStep(step_id="clarify", description="Clarify the business intent and role-sensitive constraints"),
                PlanStep(step_id="retrieve", description="Run hybrid retrieval across chunks, entities, and communities"),
                PlanStep(step_id="reflect", description="Review evidence consistency and missing risk points"),
                PlanStep(step_id="report", description="Draft a grounded answer or long-form report"),
            ],
        )


class AgentRouter:
    """Pick the appropriate agent implementation for a requested mode."""

    def __init__(self) -> None:
        self._agents = {
            "naive": NaiveRagAgent(),
            "local": GraphAgent(),
            "global": DeepResearchAgent(),
            "hybrid": HybridAgent(),
            "deep_research": DeepResearchAgent(),
            "fusion": FusionGraphRAGAgent(),
            "auto": FusionGraphRAGAgent(),
        }

    def resolve(self, requested_mode: str) -> BaseAgent:
        return self._agents.get(requested_mode or "auto", self._agents["auto"])
