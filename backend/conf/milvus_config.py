# 导入核心依赖：数据类、环境变量读取
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# 提前加载.env配置文件（必须在读取环境变量前执行，确保os.getenv能获取到值）
load_dotenv()


# 定义 Milvus 向量数据库配置
@dataclass
class MilvusConfig:
    uri: str
    collection_name: str  # 默认 Collection 名称
    ticket_collection_name: str  # 工单知识库 Collection 名称
    collection_dimension: int  # 默认维度与 Embedding 模型保持一致（Qwen3-Embedding-8B: 4096）
    index_type: str  # 使用 HNSW 索引（与 Java 项目保持一致）
    metric_type: str  # 使用 COSINE 距离度量（与 Java 项目保持一致）
    index_params: dict  # HNSW 索引参数


milvus_config = MilvusConfig(
    uri=os.getenv("MILVUS_URI", "http://127.0.0.1:19530"),
    collection_name=os.getenv("MILVUS_COLLECTION_NAME", "wendarobot"),
    ticket_collection_name=os.getenv("MILVUS_TICKET_COLLECTION_NAME", "support_ticket"),
    collection_dimension=int(os.getenv("MILVUS_COLLECTION_DIMENSION", "1024")),
    index_type=os.getenv("MILVUS_INDEX_TYPE", "HNSW"),
    metric_type=os.getenv("MILVUS_METRIC_TYPE", "COSINE"),
    index_params={
        "M": 48,
        "efConstruction": 200,
        "mmap.enabled": False
    },
)
