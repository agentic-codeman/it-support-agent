# 导入核心依赖：数据类、环境变量读取、路径处理
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# 提前加载.env配置文件（必须在读取环境变量前执行，确保os.getenv能获取到值）
# 若.env不在项目根目录，可指定路径：load_dotenv(dotenv_path=Path(__file__).parent / ".env")
load_dotenv()


# 定义minerU服务配置
@dataclass
class ModelConfig:
    base_url: str
    api_key: str
    vl_model: str
    llm_model: str
    llm_temperature: float
    rerank_base_url: str
    rerank_model: str
    system_model: str
    embedding_api_url: str
    embedding_api_key: str
    embedding_model: str
    embedding_dimension: int

model_config = ModelConfig(
    base_url=os.getenv("LLM_API_BASE"),
    api_key=os.getenv("LLM_API_KEY"),
    vl_model=os.getenv("VL_MODEL"),
    llm_model=os.getenv("LLM_MODEL"),
    llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
    rerank_base_url=os.getenv("RERANK_API_BASE"),
    rerank_model=os.getenv("RERANK_MODEL"),
    system_model=os.getenv("SYSTEM_MODEL"),
    embedding_api_url=os.getenv("EMBEDDING_API_URL"),
    embedding_api_key=os.getenv("EMBEDDING_API_KEY", ""),
    embedding_model=os.getenv("EMBEDDING_MODEL"),
    embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", "1024")),
)
