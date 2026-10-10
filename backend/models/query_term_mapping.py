"""
查询术语映射模型
用于存储用户问题术语的归一化映射规则
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, func
from backend.db.database import Base


class QueryTermMapping(Base):
    """查询术语映射表"""
    
    __tablename__ = "t_query_term_mapping"
    
    # 主键
    id = Column(String(64), primary_key=True, comment="主键ID")
    
    # 业务域/系统标识，如 biz、group、data_security 等
    domain = Column(String(100), nullable=True, comment="业务域/系统标识")
    
    # 用户原始短语
    source_term = Column(String(500), nullable=False, comment="用户原始短语")
    
    # 归一化后的目标短语
    target_term = Column(String(500), nullable=False, comment="归一化后的目标短语")
    
    # 匹配类型：1-精确匹配, 2-前缀匹配, 3-正则匹配, 4-整词匹配
    match_type = Column(Integer, default=1, comment="匹配类型：1-精确匹配, 2-前缀匹配, 3-正则匹配, 4-整词匹配")
    
    # 优先级，数值越大优先级越高（一般长词在前）
    priority = Column(Integer, default=0, comment="优先级，数值越大优先级越高")
    
    # 是否生效
    enabled = Column(Boolean, default=True, comment="是否生效")
    
    # 备注
    remark = Column(Text, nullable=True, comment="备注")
    
    # 审计字段
    create_by = Column(String(64), nullable=True, comment="创建人")
    update_by = Column(String(64), nullable=True, comment="更新人")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<QueryTermMapping(id={self.id}, source='{self.source_term}', target='{self.target_term}')>"
