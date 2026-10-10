"""
会话控制器
提供会话相关的 REST API 接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.schemas.user_context import UserContext
from backend.db.database import get_db
from backend.services import conversation_service
from backend.services.conversation_message_service import list_messages as list_messages_service
from backend.schemas.enums.conversation_message_order import ConversationMessageOrder
from backend.utils.result import Result, success_result

from backend.core.logger import logger

router = APIRouter(prefix="/conversations", tags=["会话管理"])


class ConversationUpdateRequest(BaseModel):
    """会话更新请求模型"""
    title: str = Field(..., description="会话标题")


@router.get("", response_model=Result)
async def list_conversations(db: Session = Depends(get_db)):
    """获取当前用户的会话列表

    Returns:
        Result: 包含会话列表的结果
    """
    try:
        # 获取当前用户 ID
        user_id = UserContext.get_user_id()
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        # 查询会话列表
        conversations = conversation_service.list_by_user_id(db, user_id)
        
        logger.info(f"用户 {user_id} 获取会话列表，共 {len(conversations)} 个会话")
        return success_result(data=conversations)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.put("/{conversation_id}", response_model=Result)
async def rename_conversation(conversation_id: str, request: ConversationUpdateRequest, db: Session = Depends(get_db)):
    """重命名会话

    Args:
        conversation_id: 会话 ID
        request: 更新请求

    Returns:
        Result: 操作结果
    """
    try:
        # 获取当前用户 ID
        user_id = UserContext.get_user_id()
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        # 验证标题
        title = request.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="会话名称不能为空")

        if len(title) > 128:
            raise HTTPException(status_code=400, detail="会话名称长度不能超过128个字符")

        # 重命名会话
        conversation_service.rename(db, conversation_id, user_id, title)
        
        logger.info(f"用户 {user_id} 重命名会话 {conversation_id} 为 {title}")
        return success_result(message="重命名成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"重命名会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.delete("/{conversation_id}", response_model=Result)
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """删除会话

    Args:
        conversation_id: 会话 ID

    Returns:
        Result: 操作结果
    """
    try:
        # 获取当前用户 ID
        user_id = UserContext.get_user_id()
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")

        # 删除会话
        conversation_service.delete(db, conversation_id, user_id)
        
        logger.info(f"用户 {user_id} 删除会话 {conversation_id}")
        return success_result(message="删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/{conversation_id}/messages", response_model=Result)
async def list_messages(
    conversation_id: str,
    limit: Optional[int] = Query(None, description="限制返回数量，None表示不限制"),
    order: Optional[str] = Query("ASC", description="排序方式：ASC(升序)或DESC(降序)")
):
    """获取会话消息列表
    
    Args:
        conversation_id: 会话 ID
        limit: 限制返回数量
        order: 排序方式（ASC/DESC）
        
    Returns:
        Result: 包含消息列表的结果
    """
    try:
        # 获取当前用户 ID
        user_id = UserContext.get_user_id()
        if not user_id:
            raise HTTPException(status_code=401, detail="未登录")
        
        # 转换排序参数
        message_order = ConversationMessageOrder.ASC if order.upper() == "ASC" else ConversationMessageOrder.DESC
        
        # 查询消息列表
        messages = list_messages_service(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            order=message_order
        )
        
        logger.info(f"用户 {user_id} 获取会话 {conversation_id} 的消息列表，共 {len(messages)} 条")
        return success_result(data=messages)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取消息列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
