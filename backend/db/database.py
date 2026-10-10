"""
数据库配置模块
符合 Google Python 编码规范
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.conf.database_config import database_config

# 创建数据库引擎
engine = create_engine(
    database_config.database_url,
    pool_size=database_config.pool_size,
    max_overflow=database_config.max_overflow,
    pool_recycle=database_config.pool_recycle,
    pool_timeout=database_config.pool_timeout,
    echo=database_config.echo,
)

# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建 Base 类
Base = declarative_base()


def get_db():
    """获取数据库会话（依赖注入）
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """获取数据库会话（上下文管理器方式）
    
    Returns:
        Session: 数据库会话对象，使用完毕后自动关闭
        
    Example:
        with get_db_session() as session:
            result = session.execute(stmt)
    """
    from contextlib import contextmanager
    
    @contextmanager
    def session_scope():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    return session_scope()
