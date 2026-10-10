"""
会话模型
对应数据库表 t_conversation
"""
from sqlalchemy import Column, String, Integer, DateTime, func
from backend.db.database import Base


class ConversationModel(Base):
    """会话列表"""
    
    __tablename__ = "t_conversation"
    
    # 主键
    id = Column(String(20), primary_key=True, comment="主键ID")
    
    # 业务字段
    conversation_id = Column(String(20), nullable=False, unique=True, comment="会话ID")
    user_id = Column(String(20), nullable=False, comment="用户ID")
    title = Column(String(128), nullable=False, comment="会话名称")
    last_time = Column(DateTime, nullable=True, comment="最近消息时间")
    
    # 审计字段
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted = Column(Integer, default=0, comment="是否删除 0：正常 1：删除")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"
