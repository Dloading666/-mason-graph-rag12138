"""Prompt helpers for graph extraction."""

GRAPH_EXTRACTION_PROMPT = """
你是建材知识图谱抽取助手。请从文档中抽取以下内容：
1. 实体：产品、原材料、施工工艺、合规条款、故障类型、解决方案
2. 关系：产品-原材料、产品-适用场景、工艺-合规条款、故障-解决方案
3. 输出 JSON，字段为 entities 和 relations
""".strip()

