"""
知识库数据库模型
符合 Google Python 编码规范
"""
from sqlalchemy import Column, String, DateTime, Integer, func

from backend.db.database import Base
from backend.utils.snowflake_id_utils import generate_snowflake_id_str


class KnowledgeBaseModel(Base):
    """知识库表模型"""
    __tablename__ = "t_knowledge_base"
    
    # 主键ID
    id = Column(String(20), primary_key=True, default=generate_snowflake_id_str, comment="知识库ID")
    
    # 基本信息（与 SQL 表结构保持一致）
    name = Column(String(128), nullable=False, comment="知识库名称")
    embedding_model = Column(String(64), nullable=False, comment="嵌入模型标识")
    collection_name = Column(String(64), unique=True, nullable=False, comment="Collection名称")
    
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
            "name": self.name,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }
