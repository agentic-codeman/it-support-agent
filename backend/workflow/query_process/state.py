from typing_extensions import TypedDict


class QueryGraphState(TypedDict):
    user_id : str
    conversation_id : str
    task_id: str
    question: str
    rewritten_question: str
    collection_name: str  #知识库名称
    embedding_chunks: list  # 普通向量检索回来的切片
    ticket_embedding_chunks: list # 工单解决方案的切片
    reranked_docs: list  # 重排序后的最终 Top-K 文档
    prompt: str  # 组装好的 Prompt
    answer: str  # 最终生成的答案
    history: list  # 历史对话记录
