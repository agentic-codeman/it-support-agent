"""
意图引导服务
检测用户问题的歧义并提供引导提示
"""
import re
from typing import List, Optional, Dict
from collections import OrderedDict

from backend.schemas.intent import GuidanceDecision, QuestionIntent, NodeScore, IntentNode
from backend.conf.app_config import GuidanceConfig
from backend.services.intent_node_registry import get_node_by_id
from backend.services.prompt_loader import load_prompt

from backend.core.logger import logger

# 引导提示词模板名称（对应 prompts/guidance-prompt.txt）
GUIDANCE_PROMPT_NAME = "guidance-prompt"

_config = GuidanceConfig()


def detect_ambiguity(question: str, intent: QuestionIntent) -> GuidanceDecision:
    """检测歧义

    核心逻辑：
    1. 检查配置是否启用
    2. 查找歧义组
    3. 检查是否需要跳过引导
    4. 构建引导提示

    Args:
        question: 用户问题
        intent: 问题意图

    Returns:
        GuidanceDecision: 引导决策
    """
    # 步骤1：检查配置是否启用
    if not _config.ENABLED:
        logger.debug("引导式问答功能已禁用")
        return GuidanceDecision.none()

    # 步骤2：查找歧义组
    group = _find_ambiguity_group(intent)
    if group is None or not group['option_ids']:
        logger.debug("未找到歧义组")
        return GuidanceDecision.none()

    # 步骤3：解析选项名称并检查是否需要跳过引导
    system_names = _resolve_option_names(group['option_ids'])
    if _should_skip_guidance(question, system_names):
        logger.info(f"问题中包含系统名称，跳过引导: {question}")
        return GuidanceDecision.none()

    # 步骤4：构建引导提示
    prompt = _build_prompt(group['topic_name'], group['option_ids'])
    logger.info(f"检测到歧义，生成引导提示: topic={group['topic_name']}, options={len(group['option_ids'])}")
    return GuidanceDecision.prompt(prompt)


def _find_ambiguity_group(intent: QuestionIntent) -> Optional[Dict]:
    """查找歧义组

    核心逻辑：
    1. 过滤出 KB 类型的候选意图
    2. 按名称分组
    3. 找到满足条件的最佳组

    Args:
        intent: 问题意图

    Returns:
        Optional[Dict]: 歧义组信息 {'topic_name': str, 'option_ids': List[str]}
    """
    # 过滤候选意图
    candidates = _filter_candidates(intent.node_scores)
    if len(candidates) < 2:
        logger.debug(f"候选意图数量不足2个: count={len(candidates)}")
        return None

    # 按规范化后的名称分组
    grouped: Dict[str, List[NodeScore]] = {}
    for ns in candidates:
        if not ns.node or not ns.node.name:
            continue
        normalized_name = _normalize_name(ns.node.name)
        if normalized_name not in grouped:
            grouped[normalized_name] = []
        grouped[normalized_name].append(ns)

    # 找到最佳组
    best_entry = None
    best_score = -1.0

    for key, scores in grouped.items():
        # 排序
        sorted_scores = _sort_by_score(scores)

        # 检查条件
        if len(sorted_scores) <= 1:
            continue
        if not _pass_score_ratio(sorted_scores):
            continue
        if not _has_multiple_systems(sorted_scores):
            continue

        # 比较分数
        top_score = sorted_scores[0].score
        if top_score > best_score:
            best_score = top_score
            best_entry = (key, sorted_scores)

    if best_entry is None:
        logger.debug("未找到满足条件的歧义组")
        return None

    # 构建结果
    topic_name = best_entry[1][0].node.name if best_entry[1][0].node else best_entry[0]
    option_ids = _collect_system_options(best_entry[1])

    if len(option_ids) < 2:
        logger.debug(f"选项数量不足2个: count={len(option_ids)}")
        return None

    # 限制选项数量
    trimmed_ids = _trim_options(option_ids)

    return {
        'topic_name': topic_name,
        'option_ids': trimmed_ids
    }


def _filter_candidates(scores: List[NodeScore]) -> List[NodeScore]:
    """过滤候选意图

    条件：
    1. 分数 >= INTENT_MIN_SCORE (0.35)
    2. 节点存在且为 KB 类型

    Args:
        scores: 意图评分列表

    Returns:
        List[NodeScore]: 过滤后的候选列表
    """
    if not scores:
        return []

    filtered = [
        ns for ns in scores
        if ns.score >= 0.35 and ns.node and ns.node.is_kb()
    ]
    return filtered


def _collect_system_options(group_scores: List[NodeScore]) -> List[str]:
    """收集系统选项

    从每个节点向上追溯到 CATEGORY 层级，获取系统 ID

    Args:
        group_scores: 分组后的意图评分列表

    Returns:
        List[str]: 系统 ID 列表（保持顺序，去重）
    """
    ordered = OrderedDict()

    for score in group_scores:
        node = score.node
        if not node:
            continue

        system_id = _resolve_system_node_id(node)
        if system_id:
            ordered[system_id] = True

    return list(ordered.keys())


def _resolve_system_node_id(node: IntentNode) -> Optional[str]:
    """解析系统节点 ID

    从当前节点向上追溯，找到 CATEGORY 层级的节点 ID

    Args:
        node: 意图节点

    Returns:
        Optional[str]: 系统节点 ID
    """
    if not node:
        return None

    current = node
    parent = _fetch_parent(current)

    while True:
        level = current.level  # 0=DOMAIN, 1=CATEGORY, 2=TOPIC

        # 如果是 CATEGORY 层级，且父节点是 DOMAIN 或没有父节点
        if level == 1 and (parent is None or parent.level == 0):
            return current.id

        # 如果没有父节点，返回当前节点
        if parent is None:
            return current.id

        # 继续向上追溯
        current = parent
        parent = _fetch_parent(current)


def _fetch_parent(node: IntentNode) -> Optional[IntentNode]:
    """获取父节点

    Args:
        node: 意图节点

    Returns:
        Optional[IntentNode]: 父节点
    """
    if not node or not node.parent_id:
        return None
    return get_node_by_id(node.parent_id)


def _should_skip_guidance(question: str, system_names: List[str]) -> bool:
    """检查是否应该跳过引导

    如果问题中已经包含了系统名称，则不需要引导

    Args:
        question: 用户问题
        system_names: 系统名称列表

    Returns:
        bool: 是否应该跳过
    """
    if not question or not system_names:
        return False

    normalized_question = _normalize_name(question)

    for name in system_names:
        if not name:
            continue

        # 构建别名列表
        aliases = _build_system_aliases(name)

        for alias in aliases:
            if len(alias) < 2:
                continue
            if alias in normalized_question:
                logger.debug(f"问题中包含系统名称 '{alias}'，跳过引导")
                return True

    return False


def _build_system_aliases(system_name: str) -> List[str]:
    """构建系统别名

    Args:
        system_name: 系统名称

    Returns:
        List[str]: 别名列表
    """
    if not system_name:
        return []

    normalized = _normalize_name(system_name)
    aliases = []
    if normalized:
        aliases.append(normalized)

    return aliases


def _resolve_option_names(option_ids: List[str]) -> List[str]:
    """解析选项名称

    Args:
        option_ids: 选项 ID 列表

    Returns:
        List[str]: 选项名称列表
    """
    if not option_ids:
        return []

    names = []
    for id in option_ids:
        node = get_node_by_id(id)
        if not node:
            continue
        name = node.name if node.name else node.id
        names.append(name)

    return names


def _pass_score_ratio(group: List[NodeScore]) -> bool:
    """检查分数比率是否通过

    条件：次高分 / 最高分 >= ambiguityScoreRatio (0.8)

    Args:
        group: 分组后的意图评分列表（已排序）

    Returns:
        bool: 是否通过
    """
    if len(group) < 2:
        return False

    top = group[0].score
    second = group[1].score

    if top <= 0:
        return False

    ratio = second / top
    return ratio >= _config.AMBIGUITY_SCORE_RATIO


def _has_multiple_systems(group: List[NodeScore]) -> bool:
    """检查是否有多个系统

    Args:
        group: 分组后的意图评分列表

    Returns:
        bool: 是否有多个系统
    """
    systems = set()
    for score in group:
        system_id = _resolve_system_node_id(score.node)
        if system_id:
            systems.add(system_id)

    return len(systems) > 1


def _sort_by_score(scores: List[NodeScore]) -> List[NodeScore]:
    """按分数降序排序

    Args:
        scores: 意图评分列表

    Returns:
        List[NodeScore]: 排序后的列表
    """
    return sorted(scores, key=lambda x: x.score, reverse=True)


def _trim_options(option_ids: List[str]) -> List[str]:
    """限制选项数量

    Args:
        option_ids: 选项 ID 列表

    Returns:
        List[str]: 限制后的列表
    """
    max_options = _config.MAX_OPTIONS
    if len(option_ids) <= max_options:
        return option_ids
    return option_ids[:max_options]


def _build_prompt(topic_name: str, option_ids: List[str]) -> str:
    """构建引导提示

    Args:
        topic_name: 主题名称
        option_ids: 选项 ID 列表

    Returns:
        str: 引导提示文本
    """
    options = _render_options(option_ids)

    try:
        template = load_prompt(GUIDANCE_PROMPT_NAME)
        prompt = template.replace(
            "{topic_name}", topic_name if topic_name else ""
        ).replace("{options}", options)
        return prompt
    except Exception as e:
        logger.exception(f"加载引导提示词模板失败: {e}")
        # 降级：使用简单模板
        return f"关于{topic_name}，在知识库中检索到了以下内容：\n{options}\n\n请问你具体想了解哪个？请回复数字选择（可多选，如 1,2），或回复\"都/全部\""


def _render_options(option_ids: List[str]) -> str:
    """渲染选项列表

    格式：
    1) 选项名称1
    2) 选项名称2
    ...

    Args:
        option_ids: 选项 ID 列表

    Returns:
        str: 渲染后的选项文本
    """
    lines = []
    for i, id in enumerate(option_ids):
        node = get_node_by_id(id)
        name = node.name if node and node.name else id
        lines.append(f"{i + 1}) {name}")

    return "\n".join(lines)


def _normalize_name(name: str) -> str:
    """规范化名称

    去除标点符号和空白字符，转换为小写

    Args:
        name: 原始名称

    Returns:
        str: 规范化后的名称
    """
    if not name:
        return ""

    cleaned = name.strip().lower()
    # 去除所有标点符号和空白字符（Python 不支持 \p{Punct}，用 [^\w\s] 替代）
    cleaned = re.sub(r'[^\w\s]', '', cleaned)
    cleaned = re.sub(r'\s+', '', cleaned)

    return cleaned
