"""Baseline evaluation runner for the MasonGraphRAG core."""

from __future__ import annotations

from collections import defaultdict
from time import perf_counter

from sqlalchemy.orm import Session

from backend.graphrag_core.agents.orchestrator import AgentRouter
from backend.graphrag_core.models.persistence import EvaluationRunModel


BENCHMARK_SET = [
    {
        "id": "proc-001",
        "domain": "施工规范",
        "difficulty": "basic",
        "question": "抗裂砂浆的施工合规要求有哪些？",
        "expected_keywords": ["基层", "GB", "温度"],
        "role": "normal",
    },
    {
        "id": "proc-002",
        "domain": "施工规范",
        "difficulty": "basic",
        "question": "外墙保温系统施工前要检查什么？",
        "expected_keywords": ["基层", "平整", "含水率"],
        "role": "normal",
    },
    {
        "id": "proc-003",
        "domain": "产品应用",
        "difficulty": "basic",
        "question": "瓷砖胶铺贴时满浆率要求是什么？",
        "expected_keywords": ["90%", "95%", "满浆率"],
        "role": "normal",
    },
    {
        "id": "proc-004",
        "domain": "防水",
        "difficulty": "basic",
        "question": "JS防水涂料闭水试验应如何执行？",
        "expected_keywords": ["24小时", "闭水", "渗漏"],
        "role": "normal",
    },
    {
        "id": "proc-005",
        "domain": "产品应用",
        "difficulty": "medium",
        "question": "石膏基自流平常见问题与原因有哪些？",
        "expected_keywords": ["针孔", "起粉", "空鼓"],
        "role": "normal",
    },
    {
        "id": "proc-006",
        "domain": "采购制度",
        "difficulty": "basic",
        "question": "采购审批流程里超过5万元的要求是什么？",
        "expected_keywords": ["5万元", "财务", "审批"],
        "role": "purchase",
    },
    {
        "id": "proc-007",
        "domain": "采购制度",
        "difficulty": "basic",
        "question": "水泥到场验收时重点核对哪些内容？",
        "expected_keywords": ["强度等级", "合格证", "生产日期"],
        "role": "purchase",
    },
    {
        "id": "proc-008",
        "domain": "采购制度",
        "difficulty": "medium",
        "question": "砂石雨后进场需要额外检查什么？",
        "expected_keywords": ["含水率", "复测", "含泥量"],
        "role": "purchase",
    },
    {
        "id": "proc-009",
        "domain": "施工规范",
        "difficulty": "medium",
        "question": "外墙保温锚栓安装时机和数量要求是什么？",
        "expected_keywords": ["24小时", "每平方米", "锚栓"],
        "role": "normal",
    },
    {
        "id": "proc-010",
        "domain": "施工规范",
        "difficulty": "medium",
        "question": "瓷砖胶施工后多久内应避免振动和冲击？",
        "expected_keywords": ["24小时", "振动", "冲击"],
        "role": "normal",
    },
    {
        "id": "proc-011",
        "domain": "防水",
        "difficulty": "medium",
        "question": "JS防水附加层应优先处理哪些部位？",
        "expected_keywords": ["阴阳角", "管根", "地漏"],
        "role": "normal",
    },
    {
        "id": "proc-012",
        "domain": "图谱推理",
        "difficulty": "hard",
        "question": "如果讨论外墙保温系统，图谱里通常会关联哪些施工与合规实体？",
        "expected_keywords": ["施工", "JGJ", "锚栓"],
        "role": "normal",
    },
]


class EvaluationRunner:
    """Run a benchmark suite across selected retrieval modes."""

    def __init__(self) -> None:
        self.router = AgentRouter()

    def run(self, session: Session, run: EvaluationRunModel, modes: list[str]) -> EvaluationRunModel:
        """Execute the benchmark and update the run record."""

        run.status = "running"
        per_mode: dict[str, dict[str, object]] = {}

        for mode in modes:
            total_latency_ms = 0.0
            answered = 0
            keyword_hits = 0
            evidence_hits = 0
            citation_hits = 0
            total_evidence = 0
            total_citations = 0
            domain_totals: dict[str, int] = defaultdict(int)
            domain_hits: dict[str, int] = defaultdict(int)
            case_details: list[dict[str, object]] = []

            for item in BENCHMARK_SET:
                started_at = perf_counter()
                answer = self.router.resolve(mode).run(
                    session,
                    question=item["question"],
                    user_role=item["role"],
                    requested_mode=mode,
                    need_evidence=True,
                    debug_enabled=False,
                )
                elapsed_ms = (perf_counter() - started_at) * 1000
                total_latency_ms += elapsed_ms

                answer_haystack = " ".join(
                    [
                        answer.answer,
                        " ".join(answer.citations),
                        " ".join(ev.snippet for ev in answer.evidence),
                    ]
                ).lower()
                keyword_hit = any(keyword.lower() in answer_haystack for keyword in item["expected_keywords"])
                evidence_hit = len(answer.evidence) > 0
                citation_hit = len(answer.citations) > 0

                if answer.answer:
                    answered += 1
                if keyword_hit:
                    keyword_hits += 1
                    domain_hits[item["domain"]] += 1
                if evidence_hit:
                    evidence_hits += 1
                if citation_hit:
                    citation_hits += 1

                domain_totals[item["domain"]] += 1
                total_evidence += len(answer.evidence)
                total_citations += len(answer.citations)
                case_details.append(
                    {
                        "id": item["id"],
                        "domain": item["domain"],
                        "difficulty": item["difficulty"],
                        "keyword_hit": keyword_hit,
                        "evidence_count": len(answer.evidence),
                        "citation_count": len(answer.citations),
                        "latency_ms": round(elapsed_ms, 2),
                    }
                )

            question_count = len(BENCHMARK_SET)
            domain_scores = {
                domain: round(domain_hits[domain] / total, 4)
                for domain, total in domain_totals.items()
            }
            per_mode[mode] = {
                "question_count": question_count,
                "answered_ratio": round(answered / question_count, 4),
                "keyword_hit_rate": round(keyword_hits / question_count, 4),
                "evidence_hit_rate": round(evidence_hits / question_count, 4),
                "citation_hit_rate": round(citation_hits / question_count, 4),
                "avg_latency_ms": round(total_latency_ms / question_count, 2),
                "avg_evidence_count": round(total_evidence / question_count, 2),
                "avg_citation_count": round(total_citations / question_count, 2),
                "domain_scores": domain_scores,
                "case_details": case_details,
            }

        run.status = "completed"
        run.metrics = {
            "benchmark_size": len(BENCHMARK_SET),
            "domains": sorted({item["domain"] for item in BENCHMARK_SET}),
            "modes": per_mode,
        }
        run.notes = "Benchmark completed successfully."
        return run
