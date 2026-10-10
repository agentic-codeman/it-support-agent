# 导入核心依赖：数据类、环境变量读取、路径处理
from dataclasses import dataclass
import os
from dotenv import load_dotenv


# 提前加载.env配置文件（必须在读取环境变量前执行，确保os.getenv能获取到值）
# 若.env不在项目根目录，可指定路径：load_dotenv(dotenv_path=Path(__file__).parent / ".env")
load_dotenv()


# 定义RestFS对象存储服务配置（S3兼容）
@dataclass
class RustFSConfig:
    url: str
    access_key_id: str
    secret_access_key: str
    region: str
    bucket: str
    img_dir: str  # Minio存储图片的文件夹


rustfs_config = RustFSConfig(
    url=os.getenv("RESTFS_URL"),
    access_key_id=os.getenv("RESTFS_ACCESS_KEY_ID"),
    secret_access_key=os.getenv("RESTFS_SECRET_ACCESS_KEY"),
    region=os.getenv("RESTFS_REGION"),
    bucket=os.getenv("RESTFS_BUCKET"),
    img_dir = os.getenv("RESTFS_IMG_DIR"),
)
