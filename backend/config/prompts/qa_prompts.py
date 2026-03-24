"""Prompt helpers for end-user QA."""


def build_qa_system_prompt() -> str:
    return (
        "你是建材企业内部知识助手。"
        "回答时优先引用国标编号、产品手册页码和制度名称。"
        "只根据提供的上下文作答；如果证据不足，请明确说明。"
    )


def build_qa_user_prompt(question: str, context_blocks: list[str]) -> str:
    joined_context = "\n\n".join(context_blocks) if context_blocks else "暂无可用上下文。"
    return (
        f"用户问题：{question}\n\n"
        f"候选证据：\n{joined_context}\n\n"
        "请基于候选证据生成回答，并在合适时引用其中的标准编号。"
    )
