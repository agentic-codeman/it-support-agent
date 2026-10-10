"""
会话消息模型
对应数据库表 t_message
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, func
from backend.db.database import Base


class ConversationMessageModel(Base):
    """会话消息记录表"""
    
    __tablename__ = "t_message"
    
    # 主键
    id = Column(String(20), primary_key=True, comment="主键ID")
    
    # 业务字段
    conversation_id = Column(String(20), nullable=False, comment="会话ID")
    user_id = Column(String(20), nullable=False, comment="用户ID")
    role = Column(String(16), nullable=False, comment="角色：user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")

    # 审计字段
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted = Column(Integer, default=0, comment="是否删除 0：正常 1：删除")
    
    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, role={self.role})>"
