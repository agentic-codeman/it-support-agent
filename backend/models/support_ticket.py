"""
技术支持工单数据库模型
符合 Google Python 编码规范
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, SmallInteger

from backend.db.database import Base


class SupportTicketModel(Base):
    """技术支持工单表模型

    对应数据库表: t_support_ticket
    """
    __tablename__ = "t_support_ticket"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="工单主键ticket_id")
    ticket_no = Column(String(32), nullable=False, index=True, comment="工单编号")
    title = Column(String(255), nullable=False, comment="工单标题")
    problem_desc = Column(Text, nullable=True, comment="问题现象描述")
    root_cause = Column(Text, nullable=True, comment="根因分析")
    solution = Column(Text, nullable=True, comment="解决方案")
    submitter_no = Column(String(64), nullable=False, comment="工单提出人工号")
    assignee_no = Column(String(64), nullable=True, comment="工单受理人工号")
    create_time = Column(DateTime, nullable=True, comment="提交时间")
    update_time = Column(DateTime, nullable=True, comment="工单更新时间")
    status = Column(SmallInteger, nullable=True, comment="工单状态：0待受理,1处理中,2已关闭")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "ticket_no": self.ticket_no,
            "title": self.title,
            "problem_desc": self.problem_desc,
            "root_cause": self.root_cause,
            "solution": self.solution,
            "submitter_no": self.submitter_no,
            "assignee_no": self.assignee_no,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
            "status": self.status,
        }
