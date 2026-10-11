from backend.workflow.query_process.nodes.node_search_embedding import node_search_embedding
from backend.workflow.query_process.nodes.node_search_ticket_embedding import node_search_ticket_embedding
from backend.workflow.query_process.state import QueryGraphState
from backend.core.logger import logger

# 动态 TopK 硬上限：最多取前 N 条（<=5）
RERANK_MAX_TOPK: int = 5
# 最小 TopK：至少保留前 N 条（>=1，且 <= RERANK_MAX_TOPK）
RERANK_MIN_TOPK: int = 1
# 断崖阈值（相对） 分比例
RERANK_GAP_RATIO: float = 0.25
# 断崖阈值（绝对） 分值
RERANK_GAP_ABS: float = 0.5


def step_1_rerank_docs(state: QueryGraphState):
    """
     Rerank节点
     对检索到的文档进行重新排序，提高相关性
     """
    query = state.get("rewritten_question")
    # 1. 提取输入源
    embedding_chunks = state.get("embedding_chunks") or []
    ticket_embedding_chunks = state.get("ticket_embedding_chunks") or []
    documents = []
    for hit in embedding_chunks:
        content = hit["entity"].get("content", "")
        documents.append(content)
    documents.extend(ticket_embedding_chunks)

    # 5. 使用 Qwen3-Rerank 进行精排
    from backend.utils.rerank_utils import rerank
    reranked_docs = rerank(query, documents, top_n=5)
    return reranked_docs


def step_2_topk(scored_docs):
    """
    阶段三：动态 TopK（最多 5）
    """
    max_topk = min(RERANK_MAX_TOPK, len(scored_docs))
    min_topk = RERANK_MIN_TOPK
    gap_ratio = RERANK_GAP_RATIO
    gap_abs = RERANK_GAP_ABS

    topk = max_topk
    if topk > min_topk:
        for i in range(min_topk - 1, max_topk - 1):
            s1 = scored_docs[i].get("score")
            s2 = scored_docs[i + 1].get("score")

            gap = s1 - s2
            rel = gap / (abs(s1) + 1e-6)
            if gap >= gap_abs or rel >= gap_ratio:
                logger.info(f"Step 3: 触发断崖截断 @ index={i} (Score {s1:.4f} -> {s2:.4f}, Gap={gap:.4f})")
                topk = i + 1
                break

    topk_docs = scored_docs[:topk]
    logger.info(f"Step 3: 截断完成，保留前 {len(topk_docs)} 条文档 (TopK={topk})")

    return topk_docs


def node_rerank(state: QueryGraphState):
    scored_docs = step_1_rerank_docs(state)
    topk_docs = step_2_topk(scored_docs)
    return {"reranked_docs": topk_docs}


if __name__ == "__main__":
    # 模拟测试数据
    test_state = {
        "session_id": "test_search_embedding_001",
        "item_names": ["HAK 180 烫金机"],  # 模拟已确认的商品名
        "is_stream": False,
        "collection_name": "devsupport",
        "rewritten_question": "Transformer 结构是怎样的？"
    }

    print("\n>>> 开始测试 node_search_embedding 节点...")
    try:
        # 执行节点函数
        node_search_embedding(test_state)
                # 验证结果
        chunks = test_state["embedding_chunks"]
        print(f"embedding_chunks length: {len(chunks)}")


        node_search_ticket_embedding(test_state)

        ticket_chunks =test_state["ticket_embedding_chunks"]
        print(f"ticket_embedding_chunks length: {len(ticket_chunks)}")

        # 运行节点
        result = node_rerank(test_state)
        reranked = result.get("reranked_docs", [])

        print("\n" + "=" * 50)
        print(">>> 测试结果摘要:")

        print(f"输出文档总数: {len(reranked)}")
        print("-" * 30)

        print("最终排名:")
        for i, doc in enumerate(reranked, 1):
            print(f"Rank {i}: Source={doc.get('source')}, Score={doc.get('score'):.4f}, Text={doc.get('text')[:20]}...")


        top1_score = reranked[0].get("score")
        if top1_score > 0:
            print("\n[PASS] Rerank 打分正常")
        else:
            print("\n[FAIL] Rerank 打分异常 (均为0或负数)")

        print("=" * 50)

    except Exception as e:
        logger.exception(f"测试运行期间发生未捕获异常: {e}")
