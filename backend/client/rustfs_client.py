"""RestFS 客户端封装（S3 兼容对象存储）。

请勿直接实例化 ``RestFSClient``，使用模块级单例 ``restfs_client`` 或
``get_restfs_client()`` 获取全局唯一实例。
"""
import json
import re
import shutil

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from backend.conf.rustfs_config import rustfs_config

from backend.core.logger import logger

# S3 存储桶命名规范：小写字母、数字、点号、连字符；3-63 字符；字母/数字开头结尾
_BUCKET_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")


def _validate_bucket_name(bucket_name: str) -> str:
    """校验存储桶名称是否符合 S3 命名规范，不符合时抛出 ValueError。

    桶名仅允许小写字母、数字、点号、连字符，长度 3-63，且以字母或数字
    开头和结尾。调用方需自行保证传入合法桶名，本方法不做任何转换。
    """
    if not bucket_name or not _BUCKET_NAME_PATTERN.match(bucket_name):
        raise ValueError(
            f"存储桶名称不符合 S3 规范: {bucket_name!r}"
            "（仅允许小写字母、数字、点号、连字符，3-63 字符，字母/数字开头结尾）"
        )
    return bucket_name


class RestFSClient:
    """RestFS 客户端类（基于 boto3 S3 客户端）。"""

    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=rustfs_config.url,
            aws_access_key_id=rustfs_config.access_key_id,
            aws_secret_access_key=rustfs_config.secret_access_key,
            region_name=rustfs_config.region,
        )

    def create_bucket(self, bucket_name: str) -> bool:
        """创建存储桶，已存在时返回 True。"""
        try:
            bucket_name = _validate_bucket_name(bucket_name)
            if self.bucket_exists(bucket_name):
                logger.info(f"存储桶已存在: {bucket_name}")
                return True

            self.s3_client.create_bucket(Bucket=bucket_name)
            logger.info(f"成功创建 RestFS 存储桶: {bucket_name}")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'BucketAlreadyOwnedByYou':
                logger.warning(f"存储桶已存在且属于当前用户: {bucket_name}")
                return True
            if error_code == 'BucketAlreadyExists':
                logger.error(f"存储桶已存在但由其他账户拥有: {bucket_name}")
                raise Exception(f"存储桶名称已被占用：{bucket_name}")

            logger.error(f"创建存储桶失败: {e}")
            raise Exception(f"创建存储桶失败：{str(e)}")

        except BotoCoreError as e:
            logger.error(f"RestFS 连接错误: {e}")
            raise Exception(f"RestFS 连接失败：{str(e)}")

    def bucket_exists(self, bucket_name: str) -> bool:
        """检查存储桶是否存在。"""
        try:
            self.s3_client.head_bucket(Bucket=_validate_bucket_name(bucket_name))
            return True
        except ClientError:
            return False

    def ensure_bucket_exists(self, bucket_name: str) -> bool:
        """确保存储桶存在，不存在则创建。"""
        bucket_name = _validate_bucket_name(bucket_name)
        if not self.bucket_exists(bucket_name):
            return self.create_bucket(bucket_name)
        return True

    def delete_bucket(self, bucket_name: str) -> bool:
        """删除存储桶及其中的所有对象。"""
        try:
            bucket_name = _validate_bucket_name(bucket_name)
            self._delete_all_objects(bucket_name)
            self.s3_client.delete_bucket(Bucket=bucket_name)
            logger.info(f"成功删除 RestFS 存储桶: {bucket_name}")
            return True

        except ClientError as e:
            logger.error(f"删除存储桶失败: {e}")
            raise Exception(f"删除存储桶失败：{str(e)}")

    def _delete_all_objects(self, bucket_name: str) -> None:
        """删除存储桶中的所有对象。"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in response:
                objects = [{'Key': obj['Key']} for obj in response['Contents']]
                self.s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects},
                )
                logger.info(f"已清空存储桶 {bucket_name} 中的对象")
        except ClientError as e:
            logger.warning(f"清空存储桶对象时出错: {e}")

    def upload_file(self, bucket_name: str, file_path: str, object_key: str) -> str:
        """上传本地文件到存储桶，返回对象 URL。"""
        try:
            bucket_name = _validate_bucket_name(bucket_name)
            self.s3_client.upload_file(file_path, bucket_name, object_key)
            url = f"{self.s3_client.meta.endpoint_url}/{bucket_name}/{object_key}"
            logger.info(f"成功上传文件: {object_key} 到 {bucket_name}")
            return url

        except ClientError as e:
            logger.error(f"上传文件失败: {e}")
            raise Exception(f"上传文件失败：{str(e)}")

    def upload_file_bytes(self, bucket_name: str, object_key: str, file_bytes: bytes) -> str:
        """上传字节数据到存储桶，返回对象 URL。"""
        try:
            bucket_name = _validate_bucket_name(bucket_name)
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=file_bytes,
            )
            url = f"{self.s3_client.meta.endpoint_url}/{bucket_name}/{object_key}"
            logger.info(f"成功上传字节数据: {object_key} 到 {bucket_name}")
            return url

        except ClientError as e:
            logger.error(f"上传字节数据失败: {e}")
            raise Exception(f"上传字节数据失败：{str(e)}")

    def download_file(self, bucket_name: str, object_key: str, file_path: str) -> None:
        """从存储桶下载文件到本地路径。

        使用底层 get_object 接口直接读取并写盘，而非 boto3 高层 download_file。
        原因：download_file 下载完成后会对单段对象做 MD5 与 ETag 的一致性校验，
        而 RestFS 返回的 ETag 并非标准 MD5，导致校验失败并抛出
        "did not match expected ETag"。get_object 不做该校验，可正常下载。
        """
        try:
            bucket_name = _validate_bucket_name(bucket_name)
            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_key)
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(response['Body'], f)
            logger.info(f"成功下载文件: {object_key} 从 {bucket_name}")

        except ClientError as e:
            logger.error(f"下载文件失败: {e}")
            raise Exception(f"下载文件失败：{str(e)}")

    def delete_object(self, bucket_name: str, object_key: str) -> None:
        """删除存储桶中的对象。"""
        try:
            bucket_name = _validate_bucket_name(bucket_name)
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            logger.info(f"成功删除对象: {object_key} 从 {bucket_name}")

        except ClientError as e:
            logger.error(f"删除对象失败: {e}")
            raise Exception(f"删除对象失败：{str(e)}")

    def object_exists(self, bucket_name: str, object_key: str) -> bool:
        """检查存储桶中的对象（文件）是否存在。"""
        try:
            self.s3_client.head_object(
                Bucket=_validate_bucket_name(bucket_name),
                Key=object_key,
            )
            return True
        except ClientError as e:
            # 对象不存在时返回 404 / NoSuchKey，视为不存在
            error_code = e.response.get('Error', {}).get('Code', '')
            status_code = e.response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
            if error_code in ('404', 'NoSuchKey', 'NotFound') or status_code == 404:
                return False
            # 其他错误（连接失败、权限不足等）继续抛出，交由上层处理
            logger.error(f"检查对象是否存在失败: {e}")
            raise

    def set_public_read(self, bucket_name: str, prefix: str) -> None:
        """为存储桶下的指定前缀设置公开读权限（匿名可读）。

        S3/MinIO bucket 默认私有，设置公开读后，该前缀下的对象可通过
        无签名的 URL 直接访问。
        """
        bucket_name = _validate_bucket_name(bucket_name)
        # 去掉首尾斜杠，避免构造出双斜杠的 ARN
        prefix = prefix.strip('/')
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/{prefix}/*"],
            }],
        }
        self.s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(policy),
        )
        logger.info(f"成功设置公开读权限: {bucket_name}/{prefix}/*")


# 模块级单例：模块导入时创建一次，天然单例。
restfs_client = RestFSClient()


def get_restfs_client() -> RestFSClient:
    """获取全局唯一的 RestFSClient 实例。"""
    return restfs_client


if __name__ == "__main__":
    client = get_restfs_client()
    logger.info(f"单例测试: get_restfs_client() is restfs_client -> {client is restfs_client}")
    logger.info(f"endpoint_url: {client.s3_client.meta.endpoint_url}")
