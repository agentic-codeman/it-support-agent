"""
示例问题数据库模型
对应数据库表 t_sample_question
"""
from sqlalchemy import Column, String, DateTime, Integer, text
from backend.db.database import Base


class SampleQuestionModel(Base):
    """示例问题表模型"""
    __tablename__ = 't_sample_question'

    id = Column(String(20), primary_key=True, comment='ID')
    title = Column(String(64), nullable=True, comment='展示标题')
    description = Column(String(255), nullable=True, comment='描述或提示')
    question = Column(String(255), nullable=False, comment='示例问题内容')
    create_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_time = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间')
    deleted = Column(Integer, default=0, comment='是否删除 0：正常 1：删除')
