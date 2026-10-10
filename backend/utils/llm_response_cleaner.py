"""
LLM 响应清理工具模块
"""
import re

# Markdown 代码块围栏正则表达式
_LEADING_CODE_FENCE = re.compile(r'^```[\w-]*\s*\n?')
_TRAILING_CODE_FENCE = re.compile(r'\n?```\s*$')


def strip_markdown_code_fence(raw: str) -> str:
    """移除 Markdown 代码块围栏（例如 ```json ... ```）

    Args:
        raw: 原始 LLM 响应文本

    Returns:
        str: 清理后的文本
    """
    if raw is None:
        return ""

    cleaned = raw.strip()
    cleaned = _LEADING_CODE_FENCE.sub("", cleaned)
    cleaned = _TRAILING_CODE_FENCE.sub("", cleaned)
    return cleaned.strip()
