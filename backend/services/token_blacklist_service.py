"""
Token 黑名单服务（基于 Redis）
管理 token 的黑名单操作，使用 Redis TTL 实现自动过期
符合 Google Python 编码规范
"""
import json
from datetime import datetime
from typing import Optional

import redis
from sqlalchemy.orm import Session

from backend.client.redis_client import get_redis_client as get_shared_redis_client

from backend.core.logger import logger


class TokenBlacklistService:
    """基于 Redis 的 Token 黑名单服务类"""

    @staticmethod
    def get_redis_client() -> Optional[redis.Redis]:
        """获取 Redis 客户端（复用全局共享连接池）

        Returns:
            Optional[redis.Redis]: 原生 Redis 客户端；连接失败返回 None
        """
        try:
            shared = get_shared_redis_client()
            return shared.client if shared.ping() else None
        except Exception as e:
            logger.error(f"Redis 连接失败: {str(e)}")
            return None

    @staticmethod
    def add_to_blacklist(
        db: Session,
        token: str,
        token_type: str,
        user_id: str,
        username: str,
        expires_at: datetime,
        reason: str = "logout"
    ) -> bool:
        """
        将 token 加入黑名单（使用 Redis）
        
        Args:
            db: 数据库会话（保留参数以保持接口兼容）
            token: JWT token
            token_type: token 类型 (access/refresh)
            user_id: 用户 ID
            username: 用户名
            expires_at: token 过期时间
            reason: 加入黑名单原因
            
        Returns:
            bool: 是否成功加入
        """
        redis_client = TokenBlacklistService.get_redis_client()
        if not redis_client:
            logger.error("Redis 客户端未初始化")
            return False
        
        try:
            # 计算 TTL（秒）
            now = datetime.utcnow()
            ttl_seconds = int((expires_at - now).total_seconds())
            
            # 确保至少保留一段时间（最少 1 小时）
            if ttl_seconds < 3600:
                ttl_seconds = 3600
            
            # Redis key
            key = f"token:blacklist:{token}"
            
            # 存储 token 信息
            token_info = {
                "token_type": token_type,
                "user_id": user_id,
                "username": username,
                "blacklisted_at": now.isoformat(),
                "reason": reason,
                "expires_at": expires_at.isoformat()
            }
            
            # 设置 key 和 TTL（自动过期）
            redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(token_info, ensure_ascii=False)
            )
            
            # 同时维护用户维度的索引（可选）
            user_key = f"token:blacklist:user:{user_id}"
            redis_client.sadd(user_key, token)
            redis_client.expire(user_key, ttl_seconds)
            
            logger.info(f"Token 已加入 Redis 黑名单: {username}, type={token_type}, TTL={ttl_seconds}s")
            return True
            
        except Exception as e:
            logger.exception(f"加入 Redis 黑名单失败: {str(e)}")
            return False
    
    @staticmethod
    def is_blacklisted(db: Session, token: str) -> bool:
        """
        检查 token 是否在黑名单中
        
        Args:
            db: 数据库会话（保留参数以保持接口兼容）
            token: JWT token
            
        Returns:
            bool: 是否在黑名单中
        """
        redis_client = TokenBlacklistService.get_redis_client()
        if not redis_client:
            logger.error("Redis 客户端未初始化")
            return False
        
        try:
            key = f"token:blacklist:{token}"
            exists = redis_client.exists(key)
            return exists == 1
            
        except Exception as e:
            logger.error(f"检查 Redis 黑名单失败: {str(e)}")
            return False
    
    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """
        清理已过期的黑名单记录
        
        注意：Redis 使用 TTL 自动过期，此方法仅用于兼容性
        
        Args:
            db: 数据库会话
            
        Returns:
            int: 清理的记录数（始终返回 0）
        """
        # Redis 自动处理过期，无需手动清理
        return 0
    
    @staticmethod
    def revoke_all_user_tokens(
        db: Session,
        user_id: str,
        username: str,
        reason: str = "revoke"
    ) -> int:
        """
        撤销用户的所有有效 token
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            username: 用户名
            reason: 撤销原因
            
        Returns:
            int: 撤销的 token 数量
        """
        redis_client = TokenBlacklistService.get_redis_client()
        if not redis_client:
            return 0
        
        try:
            # 获取用户的 token 列表
            user_key = f"token:blacklist:user:{user_id}"
            tokens = redis_client.smembers(user_key)
            
            # 删除所有 token
            if tokens:
                keys_to_delete = [f"token:blacklist:{token}" for token in tokens]
                redis_client.delete(*keys_to_delete)
                redis_client.delete(user_key)
                logger.info(f"已撤销用户 {username} 的 {len(tokens)} 个 token")
                return len(tokens)
            
            return 0
            
        except Exception as e:
            logger.error(f"撤销用户 token 失败: {str(e)}")
            return 0
    
    @staticmethod
    def get_user_blacklisted_tokens(
        db: Session,
        user_id: str,
        limit: int = 100
    ) -> list:
        """
        获取用户的黑名单 token 列表
        
        Args:
            db: 数据库会话
            user_id: 用户 ID
            limit: 返回数量限制
            
        Returns:
            list: 黑名单 token 列表
        """
        redis_client = TokenBlacklistService.get_redis_client()
        if not redis_client:
            return []
        
        try:
            # 获取用户的 token 列表
            user_key = f"token:blacklist:user:{user_id}"
            tokens = redis_client.smembers(user_key)
            
            # 获取每个 token 的详细信息
            result = []
            for token in list(tokens)[:limit]:
                key = f"token:blacklist:{token}"
                token_info_str = redis_client.get(key)
                if token_info_str:
                    try:
                        token_info = json.loads(token_info_str)
                        token_info['token'] = token[:50] + "..." if len(token) > 50 else token
                        result.append(token_info)
                    except:
                        pass
            
            return result
            
        except Exception as e:
            logger.error(f"获取用户黑名单 token 失败: {str(e)}")
            return []
