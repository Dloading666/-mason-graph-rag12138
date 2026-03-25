"""Persistence for mutable knowledge-base chunking and retrieval settings."""

from __future__ import annotations

import json

from backend.config.settings import settings
from backend.core.contracts import KnowledgeBaseSettings


class KnowledgeBaseSettingsStore:
    """Load and persist UI-managed settings outside the relational schema."""

    def __init__(self) -> None:
        self.path = settings.knowledge_base_settings_file
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> KnowledgeBaseSettings:
        if not self.path.exists():
            payload = KnowledgeBaseSettings()
            self.save(payload)
            return payload

        try:
            raw_payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = KnowledgeBaseSettings()
            self.save(payload)
            return payload

        return KnowledgeBaseSettings.model_validate(raw_payload)

    def save(self, payload: KnowledgeBaseSettings) -> KnowledgeBaseSettings:
        self.path.write_text(
            json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return payload
