"""
意图节点数据库模型
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, func

from backend.db.database import Base


class IntentNodeModel(Base):
    """意图节点表模型"""
    __tablename__ = "t_intent_node"
    
    # 主键ID
    id = Column(String(20), primary_key=True, comment="自增主键")
    
    # 业务字段
    kb_id = Column(String(20), nullable=True, comment="知识库ID")
    intent_code = Column(String(64), nullable=False, comment="业务唯一标识")
    name = Column(String(64), nullable=False, comment="展示名称")
    level = Column(Integer, nullable=False, comment="层级 0：DOMAIN 1：CATEGORY 2：TOPIC")
    parent_code = Column(String(64), nullable=True, comment="父节点标识")
    description = Column(String(512), nullable=True, comment="语义描述")
    examples = Column(Text, nullable=True, comment="示例问题（JSON数组字符串）")
    collection_name = Column(String(128), nullable=True, comment="关联的Collection名称")
    kind = Column(Integer, nullable=False, default=0, comment="类型 0：RAG知识库类 1：SYSTEM系统交互类")

    # 审计字段
    create_by = Column(String(20), nullable=True, comment="创建人")
    update_by = Column(String(20), nullable=True, comment="修改人")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="修改时间")
    deleted = Column(Integer, nullable=False, default=0, comment="是否删除 0：正常 1：删除")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "kb_id": self.kb_id,
            "intent_code": self.intent_code,
            "name": self.name,
            "level": self.level,
            "parent_code": self.parent_code,
            "description": self.description,
            "examples": self.examples,
            "collection_name": self.collection_name,
            "kind": self.kind,
            "create_by": self.create_by,
            "update_by": self.update_by,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
        }
