"""
FastAPI 主应用
符合 Google Python 编码规范的项目结构
"""
# 在所有导入之前禁用代理，解决 httpx proxies 参数错误
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    os.environ[key] = ''
    if key in os.environ:
        del os.environ[key]

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 配置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

from backend.db.database import engine, Base
from backend.controllers.auth import router as auth_router
from backend.controllers.user_controller import router as user_router
from backend.controllers.knowledge_controller import router as knowledge_router
from backend.controllers.document_controller import router as document_router
from backend.controllers.chunk_controller import router as chunk_router
from backend.controllers.chat_controller import router as rag_chat_router
from backend.controllers.sample_question_controller import router as sample_question_router
from backend.controllers.feedback_controller import router as feedback_router
from backend.controllers.conversation_controller import router as conversation_router
from backend.controllers.mapping_controller import router as mapping_router
from backend.controllers.intent_controller import router as intent_router
from backend.middleware.jwt_auth_middleware import JWTAuthMiddleware
from backend.middleware.user_context_middleware import UserContextCleanupMiddleware
from backend.conf.app_config import AppSettings
from backend.tasks.scheduler import start_scheduler, stop_scheduler

# 创建 FastAPI 应用
app = FastAPI(
    title=AppSettings.APP_NAME,
    description=AppSettings.APP_DESCRIPTION,
    version=AppSettings.APP_VERSION,
)

# 注册路由
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")  # user_router 包含 /users 前缀，添加 /api 后为 /api/users
app.include_router(knowledge_router)  # knowledge_router 已包含 /api/knowledge-base 前缀
app.include_router(document_router)  # document_router 已包含 /api/knowledge-base 前缀
app.include_router(chunk_router)  # chunk_router 已包含 /api/knowledge-base 前缀
app.include_router(rag_chat_router)  # rag_chat_router 已包含 /api/rag/v3 前缀
app.include_router(sample_question_router, prefix="/api")  # sample_question_router 包含 /sample-questions 前缀，添加 /api 后为 /api/sample-questions
app.include_router(feedback_router, prefix="/api")  # feedback_router 包含 /feedback 前缀，添加 /api 后为 /api/feedback
app.include_router(conversation_router, prefix="/api")  # conversation_router 包含 /conversations 前缀，添加 /api 后为 /api/conversations
app.include_router(mapping_router)  # mapping_router 已包含 /api/mappings 前缀
app.include_router(intent_router)  # intent_router 已包含 /api/intent-tree 前缀

# 注册用户上下文清理中间件（在 JWT 认证之前）
app.add_middleware(UserContextCleanupMiddleware)

# 注册认证中间件（在路由之后，CORS 之前）
app.add_middleware(JWTAuthMiddleware)

# CORS 配置（必须在最后添加，确保在最外层）
app.add_middleware(
    CORSMiddleware,
    allow_origins=AppSettings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时创建数据库表并启动定时任务调度器"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    stop_scheduler()
    print("应用关闭")


# 根路径
@app.get("/")
async def root():
    return {
        "message": "Wenda Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=AppSettings.HOST,
        port=AppSettings.PORT,
        reload=False,  # 禁用热重载以避免文件冲突
    )
