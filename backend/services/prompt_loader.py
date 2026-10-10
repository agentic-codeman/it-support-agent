"""
提示词加载器
从 backend/prompts 目录加载提示词文本，缓存在内存中。
"""
from pathlib import Path
from typing import Optional

from backend.core.logger import logger

# 提示词文件目录
PROMPT_DIR = Path(__file__).parent.parent / "prompts"

# 内存缓存：{文件名: 文件内容}
_prompt_cache: dict[str, str] = {}


def load_prompt(name: str, **kwargs) -> str:
    """加载提示词文本，可选渲染变量占位符。

    按文件名（不含扩展名）查找并读取提示词文件，结果缓存在内存中。
    若传入 kwargs，则使用 str.format 渲染占位符（如 {question}、{context}）。

    Args:
        name: 提示词文件名（不含扩展名），如 "query_rewrite"
        **kwargs: 需渲染的变量键值对

    Returns:
        str: 提示词文件内容（传入 kwargs 时为渲染后的文本）

    Raises:
        FileNotFoundError: 未找到对应的提示词文件
    """
    if name in _prompt_cache:
        content = _prompt_cache[name]
    else:
        path = _find_prompt_file(name)
        if not path:
            raise FileNotFoundError(f"提示词文件未找到: {name}")
        content = path.read_text(encoding="utf-8")
        _prompt_cache[name] = content
        logger.debug(f"成功加载提示词: {name}")

    if kwargs:
        return content.format(**kwargs)
    return content


def _find_prompt_file(name: str) -> Optional[Path]:
    """按文件名（不含扩展名）查找提示词文件。"""
    for ext in (".txt", ".st", ".prompt", ".md"):
        path = PROMPT_DIR / f"{name}{ext}"
        if path.exists():
            return path
    return None


def clear_cache() -> None:
    """清空内存缓存。"""
    _prompt_cache.clear()
    logger.info("提示词缓存已清空")
