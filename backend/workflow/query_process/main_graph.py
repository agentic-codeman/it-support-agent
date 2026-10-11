from langgraph.graph import StateGraph, END

from backend.workflow.query_process.nodes.node_intent_confirm import node_intent_confirm
from backend.workflow.query_process.nodes.node_search_embedding import node_search_embedding
from backend.workflow.query_process.nodes.node_search_ticket_embedding import node_search_ticket_embedding
from backend.workflow.query_process.nodes.node_rerank import node_rerank
from backend.workflow.query_process.nodes.node_answer_output import node_answer_output
from backend.workflow.query_process.state import QueryGraphState

builder = StateGraph(QueryGraphState)

builder.add_node("node_intent_confirm", node_intent_confirm)
builder.add_node("node_multi_search", lambda x: x)
builder.add_node("node_search_embedding", node_search_embedding)
builder.add_node("node_search_ticket_embedding", node_search_ticket_embedding)
builder.add_node("node_join", lambda x: {})
builder.add_node("node_rerank", node_rerank)
builder.add_node("node_answer_output", node_answer_output)

builder.set_entry_point("node_intent_confirm")


def route_after_item_confirm(state: QueryGraphState):
    if state.get("answer"):
        return "node_answer_output"
    return "node_multi_search"

builder.add_conditional_edges(
    "node_intent_confirm",
    route_after_item_confirm
)


builder.add_edge("node_multi_search", "node_search_embedding")
builder.add_edge("node_multi_search", "node_search_ticket_embedding")

builder.add_edge("node_search_embedding", "node_join")
builder.add_edge("node_search_ticket_embedding", "node_join")

builder.add_edge("node_join", "node_rerank")
builder.add_edge("node_rerank", "node_answer_output")
builder.add_edge("node_answer_output", END)

query_app = builder.compile()
