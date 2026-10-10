"""
消息反馈模型
对应数据库表 t_message_feedback
"""
from sqlalchemy import Column, String, Integer, DateTime, func
from backend.db.database import Base


class MessageFeedbackModel(Base):
    """会话消息反馈表"""
    
    __tablename__ = "t_message_feedback"
    
    # 主键
    id = Column(String(20), primary_key=True, comment="主键ID")
    
    # 业务字段
    message_id = Column(String(20), nullable=False, comment="消息ID")
    conversation_id = Column(String(20), nullable=False, comment="会话ID")
    user_id = Column(String(20), nullable=False, comment="用户ID")
    vote = Column(Integer, nullable=False, comment="投票 1：赞 -1：踩")
    reason = Column(String(255), nullable=True, comment="反馈原因")
    comment = Column(String(1024), nullable=True, comment="反馈评论")
    
    # 审计字段
    create_time = Column(DateTime, default=func.now(), server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted = Column(Integer, default=0, server_default="0", comment="是否删除 0：正常 1：删除")
    
    def __repr__(self):
        return f"<MessageFeedback(id={self.id}, messageId={self.message_id}, vote={self.vote})>"
