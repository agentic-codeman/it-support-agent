"""
消息反馈控制器
提供点赞、点踩等反馈功能 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.schemas.user_context import UserContext
from backend.db.database import get_db
from backend.services import message_feedback_service
from backend.utils.result import Result, success_result

from backend.core.logger import logger

router = APIRouter(prefix="/feedback", tags=["消息反馈"])


class FeedbackRequest(BaseModel):
    """反馈请求模型"""
    vote: int = Field(..., description="投票值：1=点赞，-1=点踩")
    reason: Optional[str] = Field(None, description="反馈原因（可选）")
    comment: Optional[str] = Field(None, description="补充说明（可选）")


@router.post("/message/{message_id}", response_model=Result)
async def submit_message_feedback(
    message_id: str,
    conversation_id: str,
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """提交消息反馈（点赞/点踩）
    
    Args:
        message_id: 消息ID
        conversation_id: 会话ID
        request: 反馈请求
        
    Returns:
        Result: 操作结果
    """
    try:
        # 获取当前用户ID
        user_id = UserContext.get_user_id()
        if not user_id:
            # 如果未登录，使用匿名 ID（开发环境）
            user_id = "anonymous_user"
            logger.warning(f"未检测到登录用户，使用匿名 ID: {user_id}")
        
        # 验证投票值
        if request.vote not in [1, -1]:
            raise HTTPException(status_code=400, detail="无效的投票值，必须为 1 或 -1")
        
        # 提交反馈
        success = message_feedback_service.submit_feedback(
            db=db,
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            vote=request.vote,
            reason=request.reason,
            comment=request.comment
        )
        
        if success:
            vote_text = "点赞" if request.vote == 1 else "点踩"
            logger.info(f"用户 {user_id} {vote_text}消息 {message_id}")
            return success_result(message=f"{vote_text}成功")
        else:
            raise HTTPException(status_code=500, detail="反馈提交失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"提交反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/message/{message_id}/vote", response_model=Result)
async def get_message_vote(message_id: str, db: Session = Depends(get_db)):
    """获取当前用户对指定消息的投票
    
    Args:
        message_id: 消息ID
        
    Returns:
        Result: 包含投票信息的字典 {vote: 1|-1|null}
    """
    try:
        # 获取当前用户ID
        user_id = UserContext.get_user_id()
        if not user_id:
            user_id = "anonymous_user"
        
        # 查询投票
        votes_map = message_feedback_service.get_user_votes(db, user_id, [message_id])
        
        vote = votes_map.get(message_id, None)
        
        return success_result(data={"vote": vote})
        
    except Exception as e:
        logger.exception(f"查询投票失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
