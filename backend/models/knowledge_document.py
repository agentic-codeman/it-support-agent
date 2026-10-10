"""
知识库文档数据库模型
符合 Google Python 编码规范
"""
from sqlalchemy import Column, String, DateTime, Integer, BigInteger, SmallInteger, func

from backend.db.database import Base
from backend.utils.snowflake_id_utils import generate_snowflake_id_str


class KnowledgeDocumentModel(Base):
    """知识库文档表模型"""
    __tablename__ = "t_knowledge_document"

    # 主键ID
    id = Column(String(20), primary_key=True, default=generate_snowflake_id_str, comment="文档ID")

    # 关联知识库
    kb_id = Column(String(20), nullable=False, index=True, comment="知识库ID")

    # 基本信息（匹配现有数据库表结构）
    doc_name = Column("doc_name", String(256), nullable=False, comment="文件名称")
    file_url = Column("file_url", String(512), nullable=True, comment="文件存储路径/URL")
    file_type = Column("file_type", String(16), nullable=False, comment="文件类型")
    file_size = Column("file_size", BigInteger, nullable=True, comment="文件大小（字节）")

    # 处理相关（匹配现有数据库表结构）
    status = Column("status", String(16), nullable=True, default="pending", comment="处理状态（pending, processing, success, failed）")
    chunk_count = Column("chunk_count", Integer, nullable=True, default=0, comment="分块数量")

    # 状态控制
    enabled = Column("enabled", SmallInteger, nullable=False, default=1, comment="是否启用 0：禁用 1：启用")

    # 审计字段
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
            "file_name": self.doc_name,  # 兼容前端字段名
            "title": None,  # 旧表无此字段
            "file_type": self.file_type,
            "file_path": self.file_url,  # 兼容前端字段名
            "file_size": self.file_size,
            "chunk_status": self.status,  # 兼容前端字段名
            "chunk_count": self.chunk_count,
            "chunk_fail_reason": None,  # 旧表无此字段
            "enabled": self.enabled,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }
