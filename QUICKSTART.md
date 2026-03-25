# Quick Start

这份指南只关注一件事：用最短路径把项目跑起来。

## 1. 运行前准备

请先确认本机具备：

- `Python 3.11+`
- `Node.js 20+`
- `npm`

本地快速模式默认不强依赖 `Redis`、`MinIO`、`Neo4j`。

## 2. 配置环境变量

在项目根目录复制后端配置：

```bash
cp ..env.example ..env
```

如果你使用 PowerShell：

```powershell
Copy-Item .env.example .env
```

再复制前端配置：

```bash
cp frontend/..env.example frontend/..env.local
```

至少建议补充这些变量：

```env
DASHSCOPE_API_KEY=your_api_key
# 或者分别配置
QWEN_API_KEY=your_qwen_api_key
EMBEDDING_API_KEY=your_embedding_api_key
```

说明：

- `DASHSCOPE_API_KEY` 可以同时覆盖问答模型和向量模型
- 不配模型 Key 也能启动，但回答质量和检索效果会明显下降

如果你想把本地数据库也切到 MySQL，把根目录 `.env` 里的 `DATABASE_URL` 改成：

```env
DATABASE_URL=mysql+pymysql://mason:mason_password@localhost:3306/mason_graph_rag?charset=utf8mb4
```

## 3. 启动后端

安装依赖：

```bash
pip install -r backend/requirements.txt
```

启动 API：

```bash
python -m uvicorn backend.server.api.main:app --reload --host 0.0.0.0 --port 8000
```

启动成功后可访问：

- API 根检查：`http://localhost:8000/api/health`
- Swagger：`http://localhost:8000/api/docs`

## 4. 启动前端

进入前端目录并安装依赖：

```bash
cd frontend
npm install
```

启动开发服务器：

```bash
npm run dev
```

默认地址：

- 前端工作台：`http://127.0.0.1:5173`

## 5. 登录系统

使用内置账号登录：

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `Admin@123` |
| 采购 | `buyer` | `Buyer@123` |
| 普通员工 | `staff` | `Staff@123` |

## 6. 最短验证路径

建议按这个顺序体验：

1. 登录问答页，直接提一个建材/施工问题
2. 打开“文档中心”，确认已看到内置种子文档
3. 打开“知识图谱”，确认图谱视图可加载
4. 打开“任务中心”和“Trace”页面，确认追踪链路可用

## 7. 常用本地命令

后端测试：

```bash
pytest backend/tests
```

前端打包：

```bash
cd frontend
npm run build
```

## 8. Docker 完整启动

如果你想一次性启动更完整的依赖栈：

```bash
cp ..env.example ..env
docker compose up --build
```

启动后可访问：

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Neo4j: `http://localhost:7474`
- MinIO Console: `http://localhost:9001`

注意两点：

- `docker-compose.yaml` 会为后端切换到 `MySQL + Redis + MinIO + Neo4j`
- 如果你本地不用 Docker，而是自己装 MySQL，也请把根目录 `.env` 的 `DATABASE_URL` 改成 `mysql+pymysql://...`

## 9. 常见问题

### 前端能打开，但接口报 401

先确认已经登录；后端所有核心接口都要求 Bearer Token。

### 能启动，但问答效果很弱

通常是没有配置 `QWEN_API_KEY` / `DASHSCOPE_API_KEY`，或 `EMBEDDING_API_KEY`。

### 图谱页面为空

先确认已有文档并完成入库。项目默认会同步种子文档，但若你清空了数据目录，需要重新导入文档。

### Docker 已启动 MinIO，但后端仍写本地文件

这是因为 `MINIO_ENABLED` 默认是 `false`，需要你在根目录 `.env` 中手动开启。
