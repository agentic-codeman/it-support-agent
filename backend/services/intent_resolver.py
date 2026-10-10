"""
意图解析服务
对用户问题进行意图分类，识别MCP工具和知识库意图
"""
import re
import json
from typing import List

from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langsmith import traceable

from backend.schemas.intent import QuestionIntent, NodeScore
from backend.client.llm_factory import create_chat_model
from backend.services.prompt_loader import load_prompt
from backend.services.query_rewrite_service import RewriteResult
from backend.services.intent_node_registry import load_intent_tree_data, format_leaf_nodes_for_prompt
from backend.utils.llm_response_cleaner import strip_markdown_code_fence

from backend.core.logger import logger

INTENT_MIN_SCORE = 0.35  # 意图最小置信度阈值
MAX_INTENT_COUNT = 3     # 最大意图数量

def _load_intent_classifier_prompt() -> ChatPromptTemplate:
    """加载意图分类提示词模板

    - 从项目 prompts 目录加载提示词文件
    - 支持缓存机制（LangChain 自动缓存）
    - 清理多余空行

    Returns:
        ChatPromptTemplate: LangChain 提示词模板
    """
    prompt_content = load_prompt("intent-classifier")
    cleaned_content = re.sub(r'\n{3,}', '\n\n', prompt_content).strip()

    # 创建 LangChain ChatPromptTemplate，将提示词作为 system 消息
    system_message = SystemMessagePromptTemplate.from_template(cleaned_content)
    human_message = HumanMessagePromptTemplate.from_template("{question}")
    return ChatPromptTemplate.from_messages([
        system_message,
        human_message
    ])


@traceable(name="resolve")
def resolve(rewrite_result: RewriteResult) -> QuestionIntent:
    """解析问题意图

    改写不再拆分，直接对单个问题进行意图分类。

    Args:
        rewrite_result: 查询改写结果

    Returns:
        QuestionIntent: 问题意图
    """
    question = rewrite_result.rewritten_question
    node_scores = _classify_intents(question)
    return QuestionIntent(question=question, node_scores=node_scores)


@traceable(name="_classify_intents")
def _classify_intents(question: str) -> List[NodeScore]:
    """对单个问题进行意图分类

    核心逻辑：
    1. 调用 classify_targets 获取原始意图评分列表
    2. 过滤低分意图（>= INTENT_MIN_SCORE）
    3. 限制数量（<= MAX_INTENT_COUNT）

    Args:
        question: 问题文本

    Returns:
        List[NodeScore]: 意图节点评分列表
    """
    # 步骤1：调用 classify_targets 获取所有意图评分（未过滤、未限制）
    scores = _classify_targets(question)

    filtered = [
        ns for ns in scores
        if ns.score >= INTENT_MIN_SCORE
    ]

    # 步骤3：限制最大数量
    return filtered[:MAX_INTENT_COUNT]


def is_system_only(node_scores: List[NodeScore]) -> bool:
    """判断是否仅为系统意图

    Args:
        node_scores: 节点评分列表

    Returns:
        bool: 是否仅为系统意图
    """
    return (
        len(node_scores) == 1 and
        node_scores[0].node is not None and
        node_scores[0].node.kind == "SYSTEM"
    )


@traceable(name="_classify_targets")
def _classify_targets(question: str) -> List[NodeScore]:
    """对所有叶子分类节点做意图识别

    核心逻辑：
    1. 从 IntentNodeRegistry 获取叶子节点列表
    2. 构建提示词（包含所有叶子节点信息）
    3. 调用 LLM 进行意图分类
    4. 清理 Markdown 代码块围栏
    5. 解析 JSON 响应（支持数组和对象包裹两种格式）
    6. 根据返回的 ID 获取完整的 IntentNode 对象
    7. 按分数降序排序（不过滤、不限制数量）

    Args:
        question: 问题文本

    Returns:
        List[NodeScore]: 意图节点评分列表（未过滤、未限制）
    """
    try:
        # 只加载一次意图树数据，供格式化与节点查找复用（避免多次重复读 Redis / 重建树）
        _, leaf_nodes, id_to_node = load_intent_tree_data()

        if not leaf_nodes:
            logger.warning("没有可用的意图节点，返回空列表")
            return []

        # 格式化叶子节点用于提示词
        intent_list = format_leaf_nodes_for_prompt(leaf_nodes)

        # 在使用的现场构建 LangChain 链（提示词 → LLM → JSON 解析器）
        chain = (
            _load_intent_classifier_prompt()
            | create_chat_model(temperature=0.1, top_p=0.3)
            | JsonOutputParser()
        )

        # 调用 LLM（传入 intent_list 和 question 两个参数）
        raw_result = chain.invoke({
            "intent_list": intent_list,
            "question": question
        })


        if isinstance(raw_result, str):
            cleaned_raw = strip_markdown_code_fence(raw_result)
            # 重新解析清理后的 JSON
            try:
                result = json.loads(cleaned_raw)
            except json.JSONDecodeError:
                logger.warning(f"清理 Markdown 后仍无法解析 JSON: {cleaned_raw}")
                return []
        else:
            result = raw_result

        # 容错：如果模型外面又包了一层 { "results": [...] }
        intents_data = []
        if isinstance(result, list):
            intents_data = result
            logger.info(f"[DEBUG] 解析为 list，长度: {len(intents_data)}")
        elif isinstance(result, dict) and "results" in result:
            intents_data = result.get("results", [])
            logger.info(f"[DEBUG] 解析为 dict.results，长度: {len(intents_data)}")
        else:
            logger.warning(f"LLM 返回了非预期的 JSON 格式, 类型: {type(result)}, 原始响应: {raw_result}")
            return []

        # 转换为 NodeScore 对象
        node_scores = []
        for intent in intents_data:
            if not isinstance(intent, dict):
                continue

            if "id" not in intent or "score" not in intent:
                continue

            node_id = intent.get("id")
            score = float(intent.get("score", 0))

            # 从已加载的映射中获取完整的 IntentNode 对象
            if node_id:
                node = id_to_node.get(node_id)

                if node is None:
                    logger.warning(f"LLM 返回了未知的意图节点 ID: {node_id}, 已跳过")
                    continue

                node_scores.append(NodeScore(
                    node=node,
                    score=score
                ))

        node_scores.sort(key=lambda x: x.score, reverse=True)

        if node_scores:
            logger.info(
                f"当前问题：{question}\n"
                f"意图识别结果如下所示：\n"
                f"{json.dumps([{'id': ns.node.id, 'name': ns.node.name, 'score': ns.score} for ns in node_scores], ensure_ascii=False, indent=2)}"
            )

        return node_scores

    except Exception as e:
        logger.exception(f"意图分类失败: {e}")
        return []
