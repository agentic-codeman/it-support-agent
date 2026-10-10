# 导入核心依赖：数据类、环境变量读取
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# 提前加载.env配置文件（必须在读取环境变量前执行，确保os.getenv能获取到值）
load_dotenv()


# 定义 MySQL 数据库连接配置
@dataclass
class DatabaseConfig:
    database_url: str
    pool_size: int
    max_overflow: int
    pool_recycle: int
    pool_timeout: int
    echo: bool


database_config = DatabaseConfig(
    database_url=os.getenv(
        "DATABASE_URL"
    ),
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    pool_timeout=30,  # 增加连接获取超时时间
    echo=False,
)
