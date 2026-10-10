# 导入核心依赖：数据类、环境变量读取
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# 提前加载.env配置文件（必须在读取环境变量前执行，确保os.getenv能获取到值）
load_dotenv()


# 定义 JWT 认证配置
@dataclass
class JWTConfig:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int


jwt_config = JWTConfig(
    secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
    algorithm="HS256",
    access_token_expire_minutes=1440,  # 24小时（开发环境）
    refresh_token_expire_days=7,
)
