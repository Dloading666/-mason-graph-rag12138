"""QA and graph API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.server.api.main import app
from backend.tests.conftest import auth_headers


def test_login_and_ask_question(monkeypatch):
    def fake_generate(self, messages):
        return "根据产品手册P12和GB18582-2020，需要保证基层清洁并控制施工温度。"

    monkeypatch.setattr("backend.llm.qwen_llm.QwenLLM.safe_generate_chat_completion", fake_generate)

    client = TestClient(app)
    response = client.post(
        "/api/v1/qa/ask",
        headers=auth_headers(),
        json={"question": "抗裂砂浆施工规范是什么？", "need_evidence": True, "mode": "hybrid", "debug": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["evidence"]
    assert body["trace_id"]
    assert body["mode"] == "hybrid"
    assert body["execution_summary"]["evidence_count"] >= 1


def test_purchase_only_document_hidden_from_normal_user():
    client = TestClient(app)
    response = client.get("/api/v1/documents", headers=auth_headers(username="staff", password="Staff@123"))
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert "建材采购审批流程" not in titles


def test_chinese_question_can_hit_seeded_knowledge(monkeypatch):
    monkeypatch.setattr("backend.llm.qwen_llm.QwenLLM.safe_generate_chat_completion", lambda self, messages: None)

    client = TestClient(app)
    response = client.post(
        "/api/v1/qa/ask",
        headers=auth_headers(),
        json={"question": "瓷砖胶铺贴时满浆率要求是什么？", "need_evidence": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["evidence"]
    assert any("瓷砖胶" in item["title"] for item in body["evidence"])


def test_streaming_qa_returns_sse_events(monkeypatch):
    monkeypatch.setattr(
        "backend.llm.qwen_llm.QwenLLM.safe_generate_chat_completion",
        lambda self, messages: "根据资料，建议先完成基层处理。",
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/qa/ask-stream",
        headers=auth_headers(),
        json={"question": "外墙保温系统施工前要检查什么？", "need_evidence": True},
    )
    assert response.status_code == 200
    assert "event: stage" in response.text
    assert "event: answer" in response.text
    assert "event: done" in response.text


def test_graph_endpoint_returns_communities():
    client = TestClient(app)
    response = client.get("/api/v1/graph", headers=auth_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["nodes"]
    assert "communities" in body


def test_jobs_and_traces_endpoints(monkeypatch):
    monkeypatch.setattr(
        "backend.llm.qwen_llm.QwenLLM.safe_generate_chat_completion",
        lambda self, messages: "根据资料，建议先完成基层处理。",
    )

    client = TestClient(app)
    ask_response = client.post(
        "/api/v1/qa/ask",
        headers=auth_headers(),
        json={"question": "外墙保温系统施工前要检查什么？", "need_evidence": True, "mode": "local"},
    )
    assert ask_response.status_code == 200
    trace_id = ask_response.json()["trace_id"]

    traces_response = client.get("/api/v1/traces", headers=auth_headers())
    assert traces_response.status_code == 200
    assert any(item["trace_id"] == trace_id for item in traces_response.json())

    report_response = client.post(
        "/api/v1/research/report",
        headers=auth_headers(),
        json={"question": "输出一份瓷砖胶施工长报告", "mode": "fusion"},
    )
    assert report_response.status_code == 200
    job_id = report_response.json()["job_id"]

    jobs_response = client.get("/api/v1/jobs", headers=auth_headers())
    assert jobs_response.status_code == 200
    assert any(item["job_id"] == job_id for item in jobs_response.json())


def test_admin_can_run_evaluation(monkeypatch):
    monkeypatch.setattr("backend.llm.qwen_llm.QwenLLM.safe_generate_chat_completion", lambda self, messages: None)

    client = TestClient(app)
    response = client.post(
        "/api/v1/evaluation/run",
        headers=auth_headers(),
        json={"name": "test-baseline", "modes": ["naive", "hybrid"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert "modes" in body["metrics"]
    assert body["metrics"]["benchmark_size"] >= 10
    assert "domains" in body["metrics"]
    assert "hybrid" in body["metrics"]["modes"]
