"""
知识库文档分块模型
符合 Google Python 编码规范
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, func
from backend.db.database import Base


class KnowledgeChunkModel(Base):
    """知识库文档分块表模型
    
    对应数据库表: t_knowledge_chunk
    """
    __tablename__ = "t_knowledge_chunk"
    
    id = Column(String(20), primary_key=True, comment="ID")
    kb_id = Column(String(20), nullable=False, index=True, comment="知识库ID")
    doc_id = Column(String(20), nullable=False, index=True, comment="文档ID")
    chunk_index = Column(Integer, nullable=False, comment="分块序号（从0开始）")
    content = Column(Text, nullable=False, comment="分块正文内容")
    content_hash = Column(String(64), nullable=True, comment="内容哈希（用于幂等/去重）")
    char_count = Column(Integer, nullable=True, comment="字符数")
    token_count = Column(Integer, nullable=True, comment="Token数")
    enabled = Column(Integer, nullable=False, default=1, comment="是否启用 0：禁用 1：启用")
    created_by = Column(String(20), nullable=False, comment="创建人")
    updated_by = Column(String(20), nullable=True, comment="修改人")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted = Column(Integer, nullable=False, default=0, comment="是否删除 0：正常 1：删除")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "kb_id": self.kb_id,
            "doc_id": self.doc_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "content_hash": self.content_hash,
            "char_count": self.char_count,
            "token_count": self.token_count,
            "enabled": self.enabled,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
        }
