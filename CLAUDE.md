# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Wenda Agent 是一个 Agentic RAG 智能问答系统：FastAPI 后端 + React 前端。后端通过 LangGraph 工作流编排 Milvus 向量检索、LLM 意图识别、基于提示词生成答案，并通过 SSE 流式输出。

代码注释为中文，新增注释保持一致。

## 技术栈

- **后端**：FastAPI、SQLAlchemy 2.0（MySQL via PyMySQL）、LangChain / LangGraph、pymilvus 3.0、Redis、boto3（S3 兼容的 RestFS）、loguru、schedule、snowflake-id
- **LLM**：OpenAI 兼容的 `ChatOpenAI`（主对话 / 系统意图 / 视觉多模态模型）、Ollama 向量模型（`bge-m3`）、rerank 走 HTTP API（Qwen3 rerank）
- **前端**：React 18 + Vite 5 + Tailwind CSS + Zustand + Axios + react-markdown/katex

## 常用命令

```bash
# 后端（运行在 http://localhost:5000，接口文档 /docs）
python -m backend.main

# 前端（Vite 开发服务器 :5173，/api 代理到 localhost:5000）
cd frontend && npm run dev
npm run build          # 生产构建

# Docker 一键启动全栈（MySQL、Redis、Milvus、RestFS、Ollama、后端、前端）
docker compose up -d
```

测试是仓库根目录下的独立脚本（`test_*.py`），逐个运行即可，没有 pytest 测试套件或运行器配置：

```bash
python test_rag_chat_complete.py
python test_integration.py
```

## 架构

后端在 `backend/` 下采用分层结构：

- `controllers/` — FastAPI `APIRouter`（HTTP 接口），在 `backend/main.py` 中注册。
- `services/` — 业务逻辑（意图解析、查询改写、会话记忆、知识库/文档/分块管理、token 黑名单、流式任务管理等）。
- `crud/` — SQLAlchemy 数据访问；`models/` — SQLAlchemy ORM 模型；`schemas/` — Pydantic DTO。
- `client/` — 外部客户端单例：`milvus_client`、`redis_client`、`llm_factory`、`rustfs_client`。
- `agent/` — LangGraph 工作流（见下文）。
- `conf/` — 从 `.env` 加载的 `@dataclass` 配置对象（`model_config`、`redis_config`、`rustfs_config`、`mineru_config`）。`config.py` 持有 `AppSettings`、`DatabaseConfig`、`JWTConfig`、`MilvusConfig`、`RAGConfig` 等。
- `middleware/` — `JWTAuthMiddleware`（校验 bearer token、设置 `UserContext`）和 `UserContextCleanupMiddleware`。
- `db/database.py` — SQLAlchemy `engine`、`SessionLocal`、`Base`，以及 `get_db()`（FastAPI 依赖）和 `get_db_session()`（上下文管理器）。
- `context/user_context.py` — 基于 `ContextVar` 的当前用户持有器（`UserContext`），在异步任务间传递 `user_id`/`role`，无需显式传参。
- `utils/` — 结果封装、SSE 工具、embedding/rerank 工具、雪花 ID、错误码等。
- `tasks/` — 基于 `schedule` 的后台调度器（进程内运行，每天 02:00 增量同步工单）。在 `main.py` 生命周期钩子中启动/停止。
- `prompts/` — 提示词模板文件（`.txt`、`.st`、`.prompt`），由 `services/prompt_loader.py` 的 `load_prompt(name, **kwargs)` 加载。

### 两条 LangGraph 流水线

这是系统核心。两者都是在模块导入时编译好的 `StateGraph`。

**查询流水线**（`agent/query_process/main_graph.py` → `query_app`）：

```
node_item_name_confirm
  → （条件分支）若已产出 answer → node_answer_output
  → 否则 node_multi_search（分叉）
      ├─ node_search_embedding        （知识库稠密+稀疏混合检索）
      └─ node_search_ticket_embedding （工单检索）
  → node_join → node_rerank → node_answer_output → END
```

`node_item_name_confirm` 负责加载历史、查询改写/拆分、意图解析，然后要么锁定唯一的 `collection_name`，要么直接产出歧义澄清/拒答的 `answer`（短路到输出）。状态是 `QueryGraphState`（`agent/query_process/state.py`）。

**导入流水线**（`agent/import_process/main_graph.py` → `kb_import_app`）：

```
node_entry → （条件分支：PDF / MD / 无）
  → node_pdf_to_md → node_md_img → node_document_split
  → node_bge_embedding → node_import_milvus → END
```

检索采用混合召回（稠密 `embedding` + BM25 稀疏向量），用 `RRFRanker` 融合，再可选 rerank 精排（`RAGConfig.RERANK_ENABLED`）。

### 流式问答协议

聊天在 `controllers/chat_controller.py` 中是「两步 SSE」流程：

1. `GET /api/rag/v3/chat?question=...&conversation_id=...` — 创建 `task_id` + SSE 队列，在后台线程运行 `query_app`，立即返回 `{task_id, conversation_id}`。
2. `GET /api/rag/v3/stream/{task_id}` — 客户端订阅 SSE 流。
3. `POST /api/rag/v3/stop` — 取消运行中的任务（`stream_task_manager`）。

### 认证

`JWTAuthMiddleware` 守卫除 `/api/auth/*`、`/docs`、`/openapi.json`、`/redoc`、`/health` 之外的所有路径。它解码 JWT、校验 token 黑名单（Redis 支撑）、填充 `UserContext`。token：access 24 小时、refresh 7 天。仅管理员接口使用 `middleware/jwt_auth_middleware.py` 中的 `require_admin` 依赖。

## 约定与注意事项

- **单例模式**：基础设施客户端/服务统一用「模块级单例 + `get_xxx()` 工厂函数」（如 `get_milvus_client()`、`get_redis_client()`、`get_chat_model()`）。不要直接实例化客户端；不要引入 `__new__`/双重检查锁或 `__getattr__` 桥接来做单例。
- **`backend/__init__.py` 副作用很重** — 导入任意 `backend.*` 子模块都会执行包 `__init__`，进而导入数据库引擎、模型、安全、认证控制器、中间件。尽量导入具体的叶子模块；注意 `import backend.client.milvus_client` 会触发整条链。
- **`backend/main.py` 顶部会清空代理环境变量**（`HTTP_PROXY`、`HTTPS_PROXY` 等），用于修复 httpx `proxies` 参数错误，保留该段代码。
- **`backend/unused/`** 是死代码（deepeval/ragas 评测脚本、demo 等），不要再接回去。
- **配置来自根目录 `.env`**（已 gitignore），由 `config.py` 和各 `conf/*.py` 通过 `python-dotenv` 加载。键包括 `DATABASE_URL`、`JWT_*`、`LLM_API_BASE`/`LLM_MODEL`/`SYSTEM_MODEL`/`VL_MODEL`、`EMBEDDING_API_URL`/`EMBEDDING_MODEL`、`RERANK_*`、`MILVUS_*`、`REDIS_*`、`RESTFS_*`、`MINERU_*`、`LANGSMITH_*`。切勿提交 `.env`。
- **Rerank 走 HTTP，不走 LangChain** — 见 `utils/rerank_utils.py`，不在 `client/llm_factory.py` 管理。
- **意图树** 以扁平结构存于 MySQL（`intent_node` 表），缓存在 Redis 的 `ragent:intent:tree` 键下，由 `services/intent_node_registry.py` 构建成树。
- **`ragent/`**（已 gitignore）是上游 Java 参考仓库，不是本项目源码。
