# Wenda Agent - OAuth2 + JWT 认证系统

基于登录页面图片设计的完整前后端认证系统，使用 OAuth2 + JWT 实现安全的用户认证。

## 📁 项目结构

```
wenda-agent/
├── backend/                  # 后端代码
│   ├── __init__.py
│   ├── main.py              # FastAPI 主应用
│   ├── database.py          # 数据库配置
│   ├── models.py            # 用户模型
│   ├── jwt_utils.py         # JWT 工具类
│   ├── user_service.py      # 用户服务层
│   ├── auth_controller.py   # 认证控制器
│   ├── middleware.py        # JWT 认证中间件
│   └── requirements.txt     # Python 依赖
├── frontend/                 # 前端代码
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx    # 登录页面（完美匹配图片）
│   │   │   ├── Register.jsx # 注册页面
│   │   │   └── Dashboard.jsx# 仪表板页面
│   │   ├── services/
│   │   │   └── api.js       # API 服务层
│   │   ├── store/
│   │   │   └── authStore.js # 认证状态管理
│   │   ├── App.jsx          # 路由配置
│   │   ├── main.jsx         # 入口文件
│   │   └── index.css        # 全局样式
│   ├── index.html
│   ├── package.json         # Node.js 依赖
│   ├── vite.config.js       # Vite 配置
│   ├── tailwind.config.js   # Tailwind 配置
│   └── postcss.config.js    # PostCSS 配置
├── sql/                      # 数据库脚本
│   ├── shcema_table.sql     # t_user 表结构
│   └── init_data.sql        # 初始化数据
├── result.py                 # 统一响应结果类
├── results.py                # 响应构造器
├── error_code.py             # 错误码定义
├── exceptions.py             # 自定义异常
└── .env.example              # 环境变量示例

```

## 🚀 快速开始

### 1. 环境准备

- Python 3.9+
- Node.js 16+
- MySQL 5.7+

### 2. 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 文件，修改数据库连接信息

# 启动后端服务
python main.py
```

后端服务将在 `http://localhost:8000` 启动
API 文档：`http://localhost:8000/docs`

### 3. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

## 📝 API 接口

### 认证接口

| 方法 | 路径 | 说明 | 需要认证 |
|------|------|------|----------|
| POST | /api/auth/login | 用户登录 | ❌ |
| POST | /api/auth/register | 用户注册 | ❌ |
| POST | /api/auth/refresh | 刷新令牌 | ❌ |
| GET | /api/auth/me | 获取当前用户 | ✅ |

### 请求示例

#### 登录
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "123456",
    "remember_me": true
  }'
```

#### 注册
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "password123",
    "confirm_password": "password123"
  }'
```

#### 刷新令牌
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your-refresh-token"
  }'
```

#### 获取当前用户
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer your-access-token"
```

## 🔐 认证流程

1. **登录**：用户提供用户名和密码，服务器验证后返回 access_token 和 refresh_token
2. **访问受保护资源**：在请求头中携带 `Authorization: Bearer <access_token>`
3. **令牌刷新**：access_token 过期后，使用 refresh_token 获取新的 access_token
4. **退出登录**：清除本地存储的 token 和用户信息

## 🎨 前端特性

- ✅ 完美匹配登录页面图片设计
- ✅ 响应式布局，支持移动端
- ✅ 表单验证和错误提示
- ✅ 密码显示/隐藏切换
- ✅ 记住我功能
- ✅ 自动 token 刷新
- ✅ 路由守卫
- ✅ 状态持久化

## 🔧 技术栈

### 后端
- **FastAPI** - 高性能 Python Web 框架
- **SQLAlchemy** - ORM 数据库操作
- **PyJWT** - JWT 令牌处理
- **Passlib** - 密码加密
- **MySQL** - 数据库

### 前端
- **React 18** - 用户界面库
- **Vite** - 构建工具
- **React Router** - 路由管理
- **Tailwind CSS** - 原子化 CSS 框架
- **Zustand** - 状态管理
- **Axios** - HTTP 客户端
- **Lucide React** - 图标库

## 📦 数据库表结构

### t_user 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 ID |
| username | varchar(64) | 用户名（唯一） |
| password | varchar(128) | 密码（加密存储） |
| role | varchar(32) | 角色（admin/user） |
| avatar | varchar(128) | 用户头像 |
| create_time | datetime | 创建时间 |
| update_time | datetime | 更新时间 |
| deleted | tinyint | 是否删除（0:正常 1:删除） |

## 🔒 安全特性

- ✅ 密码使用 bcrypt 加密存储
- ✅ JWT 令牌签名验证
- ✅ HTTP Only Cookie 存储 refresh_token
- ✅ CORS 跨域配置
- ✅ 请求频率限制（可选）

## 🆕 最新功能：Milvus 混合检索 + Ollama Rerank

### 概述

本项目现已支持 **Milvus 混合检索** 与 **Ollama Rerank** 的集成，实现了三层检索架构：

1. **多通道召回**：稠密向量（语义）+ 稀疏向量（关键词）
2. **RRF 排名融合**：Reciprocal Rank Fusion 算法
3. **Ollama Rerank 精排**：本地 BGE-Reranker-v2-M3 模型

### 快速开始

```bash
# 1. 启动 Ollama 并拉取模型
ollama serve
ollama pull bge-reranker-v2-m3

# 2. 运行测试
python test_ollama_rerank.py              # 测试 Rerank API
python test_milvus_hybrid_search.py       # 完整混合检索测试
```

### 相关文档

- 📖 [快速启动指南](./QUICK_START_OLLAMA_RERANK.md)
- 📚 [完整使用文档](./MILVUS_HYBRID_SEARCH_WITH_OLLAMA_RERANK.md)
- 📝 [实施总结](./IMPLEMENTATION_SUMMARY_OLLAMA_RERANK.md)

### 核心特性

- ✅ 本地部署，隐私安全
- ✅ 显著提升检索准确率（+15-25%）
- ✅ 灵活配置，可选择启用/禁用
- ✅ 完善的错误处理和降级策略
- ✅ 详细的文档和示例
- ✅ Access Token 有效期 24 小时
- ✅ Refresh Token 有效期 7 天
- ✅ 支持"记住我"功能（延长 token 有效期）
- ✅ 自动 token 刷新机制
- ✅ CORS 跨域配置
- ✅ 请求拦截器自动携带 token
- ✅ 响应拦截器自动处理 401 错误

## 📖 使用说明

1. 首次使用请先注册账号
2. 登录时勾选"记住我"可延长 token 有效期到 7 天
3. 账号由管理员初始化（注册页面提供自助注册功能）
4. 登录后可以访问仪表板查看用户信息
5. 点击"退出登录"清除认证信息

## 🐛 常见问题

### 数据库连接失败
检查 `.env` 文件中的 `DATABASE_URL` 配置是否正确

### 前端请求 401 错误
检查 token 是否过期，系统会自动尝试刷新 token

### CORS 错误
确保后端 `main.py` 中的 `allow_origins` 包含前端地址

## 📄 许可证

MIT License
