"""Lightweight entity extraction for graph previews."""

from __future__ import annotations

import re

from backend.core.contracts import DocumentRecord


STANDARD_PATTERN = re.compile(r"GB\s?\d+(?:\.\d+)?-\d{4}")
PRODUCT_KEYWORDS = ("砂浆", "水泥", "保温", "涂料", "腻子")
PROCESS_KEYWORDS = ("施工", "搅拌", "审批", "比价", "基层")


class EntityExtractor:
    """Extract coarse entities without requiring an online LLM."""

    def extract(self, document: DocumentRecord) -> list[dict[str, str]]:
        entities: list[dict[str, str]] = []
        for match in STANDARD_PATTERN.findall(document.content):
            entities.append({"name": match.replace(" ", ""), "category": "合规条款"})

        for keyword in PRODUCT_KEYWORDS:
            if keyword in document.content or keyword in document.title:
                entities.append({"name": keyword, "category": "产品"})

        for keyword in PROCESS_KEYWORDS:
            if keyword in document.content:
                entities.append({"name": keyword, "category": "施工工艺"})

        return entities

