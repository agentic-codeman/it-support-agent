from backend.workflow.query_process.nodes.node_search_embedding import node_search_embedding
from backend.workflow.query_process.nodes.node_search_ticket_embedding import node_search_ticket_embedding
from backend.workflow.query_process.state import QueryGraphState
from backend.core.logger import logger

def node_rerank(state: QueryGraphState):
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

  return {"reranked_docs": reranked_docs}


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
