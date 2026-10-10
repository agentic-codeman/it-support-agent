"""
应用配置管理模块
符合 Google Python 编码规范
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class AppSettings:
    """应用设置类"""
    
    APP_NAME: str = "Wenda Agent API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "问答代理系统 API - OAuth2 + JWT 认证"
    
    # CORS 配置（覆盖 Vite 开发服务器所有可能端口）
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
    ]
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    RELOAD: bool = True


class RAGConfig:
    """RAG 系统功能配置类"""
    
    # 查询重写功能开关
    # 控制是否启用查询重写功能，查询重写可以将用户的查询语句优化为更适合检索的形式
    QUERY_REWRITE_ENABLED: bool = os.getenv("RAG_QUERY_REWRITE_ENABLED", "true").lower() == "true"
    
    # 改写时用于承接上下文的最大历史消息数
    QUERY_REWRITE_MAX_HISTORY_MESSAGES: int = int(os.getenv("RAG_QUERY_REWRITE_MAX_HISTORY_MESSAGES", "4"))
    
    # 改写时用于承接上下文的最大字符数
    QUERY_REWRITE_MAX_HISTORY_CHARS: int = int(os.getenv("RAG_QUERY_REWRITE_MAX_HISTORY_CHARS", "500"))
    
    # Rerank 重排功能开关
    # 控制是否在混合检索后使用 Qwen3-Rerank 进行精排，关闭则直接返回 RRF 融合结果
    RERANK_ENABLED: bool = os.getenv("RERANK_ENABLED", "true").lower() == "true"


class GuidanceConfig:
    """意图引导配置类"""
    
    # 是否启用引导式问答
    ENABLED: bool = os.getenv("RAG_GUIDANCE_ENABLED", "true").lower() == "true"
    
    # 触发引导式问答的最低分数相对阈值（次高分 >= 最高分 * ratio）
    AMBIGUITY_SCORE_RATIO: float = float(os.getenv("RAG_GUIDANCE_AMBIGUITY_SCORE_RATIO", "0.8"))
    
    # 单次最多展示的选项数量
    MAX_OPTIONS: int = int(os.getenv("RAG_GUIDANCE_MAX_OPTIONS", "6"))
