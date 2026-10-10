from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START

from backend.workflow.import_process.state import ImportGraphState, create_default_state
from backend.workflow.import_process.nodes.node_entry import node_entry
from backend.workflow.import_process.nodes.node_pdf_to_md import node_pdf_to_md
from backend.workflow.import_process.nodes.node_md_img import node_md_img
from backend.workflow.import_process.nodes.node_document_split import node_document_split
from backend.workflow.import_process.nodes.node_bge_embedding import node_bge_embedding
from backend.workflow.import_process.nodes.node_import_milvus import node_import_milvus

load_dotenv()

workflow = StateGraph(ImportGraphState)

workflow.add_node("node_entry", node_entry)
workflow.add_node("node_pdf_to_md", node_pdf_to_md)
workflow.add_node("node_md_img", node_md_img)
workflow.add_node("node_document_split", node_document_split)
workflow.add_node("node_bge_embedding", node_bge_embedding)
workflow.add_node("node_import_milvus", node_import_milvus)

workflow.set_entry_point("node_entry")

def route_after_entry(state: ImportGraphState) -> str:
    if state.get("is_md_read_enabled"):
        return "node_md_img"
    elif state.get("is_pdf_read_enabled"):
        return "node_pdf_to_md"
    else:
        return END

workflow.add_conditional_edges(
    "node_entry",
    route_after_entry,
    {
        "node_md_img": "node_md_img",
        "node_pdf_to_md": "node_pdf_to_md",
        END: END
    }
)

workflow.add_edge("node_pdf_to_md", "node_md_img")
workflow.add_edge("node_md_img", "node_document_split")
workflow.add_edge("node_document_split", "node_bge_embedding")
workflow.add_edge("node_bge_embedding", "node_import_milvus")
workflow.add_edge("node_import_milvus", END)

kb_import_app = workflow.compile()