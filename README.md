# 匠图智答 · 建材图谱智能问答平台

面向建材与施工场景的企业私有知识问答平台，结合文档检索、图谱关联和可追踪证据链，提供可落地的 GraphRAG 工作台。

这是一个前后端分离的完整项目：

- 前端使用 `React + Vite + TypeScript + Ant Design`
- 后端使用 `FastAPI`
- 默认支持本地轻量运行，也支持通过 `Docker Compose` 启动更完整的后端依赖
- 内置种子文档、角色权限、问答追踪、知识图谱可视化、异步任务与评估能力

快速开始请直接看 [QUICKSTART.md](./QUICKSTART.md)。

## 项目亮点

- 多模式问答：支持 `naive`、`local`、`global`、`hybrid`、`fusion` 等检索/推理模式
- 证据优先：每次回答都可返回引用、证据片段、Trace ID
- 图谱联动：支持知识图谱视图、社区摘要、实体邻居关系
- 知识库治理：支持文档上传、切块预览、检索参数调优、召回测试
- 角色权限：内置管理员、采购、普通员工三类角色
- 任务中心：支持文档入库任务、研究报告任务、任务状态追踪
- 评估面板：可对不同检索模式进行基线评估
- 本地友好：默认使用 `SQLite + 本地文件存储 + 同步/即时任务`，方便快速体验

## 适用场景

- 建材产品知识库问答
- 施工规范与工艺说明检索
- 采购制度与审批流程查询
- 企业私有资料的角色化访问与问答审计
- 需要将结构化图谱与非结构化文档联动的内部知识平台

## 系统架构

```mermaid
flowchart LR
    A["React Frontend"] --> B["FastAPI API"]
    B --> C["SQLite / MySQL"]
    B --> D["Local Storage / MinIO"]
    B --> E["SQLite Graph Artifacts / Neo4j"]
    B --> F["DashScope-compatible LLM"]
    B --> G["Embedding Service"]
    B --> H["Celery / Immediate Tasks"]
```

### 默认本地模式

- 数据库：`SQLite`
- 对象存储：本地文件系统
- 异步任务：Celery eager / 立即执行
- 图谱查询：SQL 回退路径

### Docker Compose 模式

- 数据库：`MySQL 8`
- 队列：`Redis`
- 图数据库：`Neo4j`
- 对象存储：`MinIO`
- 后端：`FastAPI + Celery Worker`
- 前端：`Nginx` 托管打包产物

## 功能模块

### 1. 问答工作台

- 标准回答、流式回答、调试模式
- 证据面板、引用标签、计划与执行摘要
- 支持生成长文本研究报告

### 2. 文档中心

- 支持上传并入库文档
- 支持切块预览、检索测试、知识库配置调整
- 支持按角色控制文档可见性

当前支持的文档类型：

- `txt`
- `md`
- `csv`
- `json`
- `yaml`
- `yml`
- `pdf`
- `docx`
- `doc`
- `xlsx`

### 3. 知识图谱

- 文档节点、实体节点、关系边
- 社区摘要与邻居关系展示
- `Neo4j` 可用时优先走图查询，否则自动回退到 SQL 产物

### 4. 任务与审计

- 文档入库任务
- 研究报告任务
- Trace 审计记录
- 用户反馈提交

### 5. 评估与治理

- 基线评估运行
- 模式对比
- 评估结果持久化

## 技术栈

### Frontend

- `React 18`
- `TypeScript`
- `Vite`
- `Ant Design`
- `ECharts`
- `Framer Motion`

### Backend

- `FastAPI`
- `Pydantic v2`
- `SQLAlchemy`
- `Celery`
- `Redis`
- `Neo4j`
- `boto3 / MinIO`

### Model & Retrieval

- `Qwen` 兼容接口
- DashScope 兼容 Embedding 接口
- GraphRAG 风格的多路检索与证据聚合

## 仓库结构

```text
.
├─ backend/                  # FastAPI、GraphRAG 核心、服务层、测试
│  ├─ server/                # API 路由与服务
│  ├─ graphrag_core/         # 图谱、任务、评估、运行时
│  ├─ pipelines/             # 文档处理与入库流程
│  ├─ llm/                   # LLM 接入
│  ├─ embedding/             # 向量模型接入
│  └─ tests/                 # 后端测试
├─ frontend/                 # React 控制台
│  ├─ src/pages/             # 页面：问答、文档、图谱、任务、审计、设置
│  ├─ src/components/        # UI 组件
│  └─ src/api/               # API 封装
├─ docker-compose.yaml       # 完整部署编排
├─ .env.example              # 后端环境变量示例
└─ QUICKSTART.md             # 最短启动指南
```

## 启动方式

### 方式一：本地快速运行

适合开发、调试和快速演示，不依赖 Redis、MinIO、Neo4j。

1. 复制根目录环境变量文件
2. 配置模型与向量服务 Key
3. 如需本地接入 MySQL，将 `DATABASE_URL` 改为 `mysql+pymysql://...`
4. 启动后端
5. 启动前端

详见 [QUICKSTART.md](./QUICKSTART.md)。

### 方式二：Docker Compose 完整运行

```bash
cp ..env.example ..env
docker compose up --build
```

启动后默认访问：

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/api/docs`
- Neo4j Browser: `http://localhost:7474`
- MinIO Console: `http://localhost:9001`

注意：

- `docker-compose.yaml` 已为后端启用 `MySQL`、`Redis`、`MinIO`、`Neo4j`
- 大模型和向量服务相关 Key 仍需通过根目录 `.env` 提供

## 默认账号

系统内置了 3 个种子账号，便于本地演示：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `Admin@123` |
| 采购 | `buyer` | `Buyer@123` |
| 普通员工 | `staff` | `Staff@123` |

## 环境变量说明

以下变量最关键：

| 变量名 | 说明 |
| --- | --- |
| `DASHSCOPE_API_KEY` | 可同时作为 Qwen 与 Embedding 的通用 Key |
| `QWEN_API_KEY` | 单独指定问答模型 Key，可选 |
| `EMBEDDING_API_KEY` | 单独指定向量模型 Key，可选 |
| `DATABASE_URL` | 本地默认是 SQLite，也可以改成 MySQL；Compose 下默认切到 MySQL |
| `MINIO_ENABLED` | 是否启用 MinIO，对本地模式默认关闭 |
| `NEO4J_ENABLED` | 是否启用 Neo4j，本地默认关闭 |
| `CELERY_TASK_ALWAYS_EAGER` | 是否立即执行任务，本地默认开启 |
| `ALLOWED_ORIGINS` | 前端跨域白名单 |

说明：

- 如果未配置 `QWEN_API_KEY` 或 `DASHSCOPE_API_KEY`，系统会尝试回退到本地答案生成逻辑，但效果会明显受限
- 如果未配置 `EMBEDDING_API_KEY`，检索会回退到关键词优先模式
- MySQL 推荐连接串格式：`mysql+pymysql://mason:mason_password@localhost:3306/mason_graph_rag?charset=utf8mb4`

## 种子数据

应用启动时会自动初始化数据库，并尝试从 `backend/data/state/documents.json` 同步种子文档记录。仓库中已经带有若干建材与施工相关示例文档，适合开箱即用演示。

## API 概览

核心接口前缀为 `http://localhost:8000/api/v1`。

| 模块 | 主要接口 |
| --- | --- |
| 认证 | `/auth/login` |
| 问答 | `/qa/ask`、`/qa/ask-stream` |
| 研究报告 | `/research/report` |
| 文档治理 | `/documents`、`/documents/upload`、`/documents/{id}/ingest` |
| 检索调优 | `/documents/settings`、`/documents/retrieval-test` |
| 图谱 | `/graph` |
| 任务 | `/jobs` |
| 审计 | `/traces`、`/feedback` |
| 评估 | `/evaluation/run`、`/evaluation` |

完整接口请查看：

- `http://localhost:8000/api/docs`
- `http://localhost:8000/api/redoc`

## 开发与测试

### 后端测试

```bash
pytest backend/tests
```

### 前端打包

```bash
cd frontend
npm run build
```

## 发布到 GitHub 前的建议

- 确认 `.env`、`frontend/.env.local` 没有提交
- 确认 `node_modules/`、`dist/`、`backend/data/` 等本地产物按需处理
- 建议补充 `LICENSE`
- 如果准备公开演示，建议替换默认账号密码与 JWT 密钥

## 后续可扩展方向

- 接入企业统一身份认证
- 增加更细粒度的文档权限模型
- 引入更多评估集与自动回归流程
- 增加知识图谱构建监控与质量诊断
