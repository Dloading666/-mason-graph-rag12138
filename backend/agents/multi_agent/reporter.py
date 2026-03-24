"""Reporter agent scaffold."""

from __future__ import annotations

from backend.core.evidence import EvidenceItem


class ReporterAgent:
    def report(self, question: str, evidence: list[EvidenceItem]) -> str:
        if not evidence:
            return f"问题“{question}”暂无足够证据。"
        lines = [f"问题：{question}", "关键证据："]
        lines.extend(f"- {item.title}: {item.snippet}" for item in evidence)
        return "\n".join(lines)

