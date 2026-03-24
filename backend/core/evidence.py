"""Evidence models returned by QA flows."""

from backend.core.base_model import MasonBaseModel


class EvidenceItem(MasonBaseModel):
    title: str
    source: str
    snippet: str
    citation: str
    score: float

