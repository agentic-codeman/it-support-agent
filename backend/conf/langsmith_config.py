# 导入核心依赖：数据类、环境变量读取
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# 提前加载.env配置文件（必须在读取环境变量前执行，确保os.getenv能获取到值）
load_dotenv()


# 定义 LangSmith 评测与追踪配置
@dataclass
class LangSmithConfig:
    api_key: str  # LangSmith API Key（https://smith.langchain.com/settings/api-keys）
    project: str  # LangSmith 项目名称
    tracing_enabled: bool  # 是否启用自动 Tracing（LangChain 调用自动上传到 LangSmith）
    endpoint: str  # LangSmith API 端点（SaaS 无需修改，自托管时配置）


langsmith_config = LangSmithConfig(
    api_key=os.getenv("LANGSMITH_API_KEY", ""),
    project=os.getenv("LANGSMITH_PROJECT", "wenda-agent"),
    tracing_enabled=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
    endpoint=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
)
