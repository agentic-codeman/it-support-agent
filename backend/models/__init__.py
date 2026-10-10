"""
数据库模型层
包含所有 SQLAlchemy ORM 模型定义
符合 Google Python 编码规范
"""
from backend.models.user import UserModel
from backend.models.knowledge_base import KnowledgeBaseModel
from backend.models.knowledge_document import KnowledgeDocumentModel
from backend.models.knowledge_chunk import KnowledgeChunkModel
from backend.models.conversation import ConversationModel
from backend.models.conversation_message import ConversationMessageModel
from backend.models.conversation_summary import ConversationSummaryModel
from backend.models.support_ticket import SupportTicketModel

__all__ = [
    "UserModel",
    "KnowledgeBaseModel",
    "KnowledgeDocumentModel",
    "KnowledgeChunkModel",
    "ConversationModel",
    "ConversationMessageModel",
    "ConversationSummaryModel",
    "SupportTicketModel",
]
