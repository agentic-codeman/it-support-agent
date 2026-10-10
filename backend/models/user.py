"""
用户数据库模型
符合 Google Python 编码规范
"""
from sqlalchemy import Column, String, DateTime, Integer, func

from backend.db.database import Base
from backend.utils.snowflake_id_utils import generate_snowflake_id_str


class UserModel(Base):
    """用户表模型"""
    __tablename__ = "t_user"
    
    # 使用 VARCHAR(20) 存储雪花算法生成的 ID
    id = Column(String(20), primary_key=True, default=generate_snowflake_id_str, comment="主键ID")
    username = Column(String(64), unique=True, nullable=False, comment="用户名，唯一")
    password = Column(String(128), nullable=False, comment="密码")
    role = Column(String(32), nullable=False, default="user", comment="角色：admin/user")
    avatar = Column(String(128), nullable=True, comment="用户头像")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted = Column(Integer, default=0, comment="是否删除 0：正常 1：删除")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "avatar": self.avatar,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
        }
