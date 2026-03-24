"""Static constants for the MasonGraphRAG backend."""

CHUNK_SIZE = 800
OVERLAP = 150
MAX_TEXT_LENGTH = 20_000

MASON_ENTITY_TYPES = [
    "product",
    "material",
    "process",
    "compliance",
    "failure",
    "solution",
]
MASON_RELATION_TYPES = [
    "related_to",
    "applies_to",
    "complies_with",
    "resolved_by",
]
USER_ROLES = ["normal", "purchase", "admin"]

DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_QWEN_MODEL = "qwen3.5-plus"
DEFAULT_EMBEDDING_MODEL = "text-embedding-v4"
DEFAULT_EMBEDDING_DIMENSION = 1024
DEFAULT_QWEN_TEMPERATURE = 0.1
DEFAULT_QWEN_MAX_TOKENS = 1200
DEFAULT_QWEN_TIMEOUT_SECONDS = 60
DEFAULT_EMBEDDING_TIMEOUT_SECONDS = 30

ROLE_LABELS = {
    "normal": "Normal Staff",
    "purchase": "Purchase",
    "admin": "Administrator",
}
