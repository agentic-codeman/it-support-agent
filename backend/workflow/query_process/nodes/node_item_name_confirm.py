from typing import List

from backend.workflow.query_process.state import QueryGraphState
from dotenv import load_dotenv, find_dotenv
from backend.core.logger import logger
from backend.schemas.chat import ChatMessage
from backend.schemas.intent import QuestionIntent, NodeScore
from backend.services.conversation_memory_service import load_and_append
from backend.services.intent_resolver import resolve, is_system_only
from backend.services.query_rewrite_service import rewrite_with_split
from backend.services.intent_guidance_service import detect_ambiguity

load_dotenv(find_dotenv())


def step_4_check_confirmation(state: QueryGraphState, intent: QuestionIntent):
    all_system_only = is_system_only(intent.node_scores)
    if all_system_only:
        # TODO  使用系统提示词回答
        state["answer"] = "你好，我是智能问答系统"
    else:
        candidates = filter_candidates(intent.node_scores)
        if len(candidates) == 0:
            state["answer"] = "抱歉，问题已超出系统范围，请到工单系统提单"
        elif len(candidates) == 1:
            state["collection_name"] = candidates[0].node.collection_name
        else:
            guidance_decision = detect_ambiguity(intent.question, intent)
            if not guidance_decision.is_prompt():
                state["collection_name"] = candidates[0].node.collection_name
            else:
                state["answer"] = guidance_decision.prompt


def filter_candidates(scores: List[NodeScore]) -> List[NodeScore]:
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


def sort_by_score(scores: List[NodeScore]) -> List[NodeScore]:
    """按分数降序排序

    Args:
        scores: 意图评分列表

    Returns:
        List[NodeScore]: 排序后的列表
    """
    return sorted(scores, key=lambda x: x.score, reverse=True)


def node_item_name_confirm(state: QueryGraphState) -> QueryGraphState:
    logger.info(">>> node_item_name_confirm: 开始处理")

    question = state.get("question", "")
    conversation_id = state["conversation_id"];
    user_id = state["user_id"];

    # 1. 获取历史记录
    user_message = ChatMessage(role="user", content=question)
    history = load_and_append(
        conversation_id=conversation_id,
        user_id=user_id,
        new_message=user_message
    )
    logger.info(f"Node: 获取到 {len(history)} 条历史消息")
    state["history"] = history

    # 2. 查询改写与拆分
    rewrite_result = rewrite_with_split(question, history)

    state["rewritten_question"] = rewrite_result.rewritten_question

    # 3. 意图解析
    intent = resolve(rewrite_result)

    step_4_check_confirmation(state, intent)

    logger.info(f"Node: 处理结束, query collection name: {state.get('collection_name')}")
    return state


if __name__ == "__main__":
    # 测试代码块
    print("\n" + "="*50)
    print(">>> 启动 node_item_name_confirm 本地测试")
    print("="*50)
    
    # 模拟输入状态
    mock_state = {
        "conversation_id": "876014823492685829",
        "user_id": "17765301953665238",
        "question": "你好",  # 针对用户提到的具体 case
        "is_stream": False,
        "item_names": []
    }

    try:
        # 运行节点
        result = node_item_name_confirm(mock_state)
        
        print("\n" + "="*50)
        print(">>> 测试结果摘要:")
        print(f"Answer: {result.get('answer')}")
        print("="*50)

    except Exception as e:
        logger.exception(f"测试运行期间发生未捕获异常: {e}")
