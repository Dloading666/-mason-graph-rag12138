# 匠图智答（MasonGraphRAG）

面向建材企业内网场景的私有化智能问答骨架，采用 `FastAPI + React + Ant Design`，并预留阿里百炼 Qwen / Embedding、知识图谱和多 Agent 扩展点。

## 当前版本能力

- 本地 JWT 账号登录与角色鉴权（`normal` / `purchase` / `admin`）
- 建材问答主链路：问题输入、文档检索、证据链返回、引用提取
- 文档上传 / 列表 / 删除 / 增量入库接口
- 图谱只读查询接口与前端可视化页面
- DashScope 兼容模式接入 `qwen3.5-plus` 与 `text-embedding-v4`
- 无模型密钥时自动退化为本地抽取式回答，方便内网骨架先跑通

## 快速启动

### 后端

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.server.api.main:app --reload
```

默认地址：`http://localhost:8000/api/docs`

### 前端

```bash
cd frontend
npm install
npm run dev
```

默认地址：`http://localhost:5173`

### Docker

```bash
docker compose up --build
```

如需同时启动 Neo4j 图谱服务，请改用：

```bash
docker compose --profile graph up --build
```

## 默认账号

- 管理员：`admin / Admin@123`
- 采购岗：`buyer / Buyer@123`
- 普通员工：`staff / Staff@123`

## 关键环境变量

参考根目录 `.env.example`。

- `QWEN_API_KEY`: 大模型专用 API Key
- `EMBEDDING_API_KEY`: Embedding 专用 API Key
- `DASHSCOPE_API_KEY`: 公共兜底 API Key，只有在未单独配置上面两个变量时才会使用
- `QWEN_MODEL`: 默认 `qwen3.5-plus`
- `EMBEDDING_MODEL`: 默认 `text-embedding-v4`
- `EMBEDDING_DIMENSION`: 默认 `1024`
- `JWT_SECRET_KEY`: JWT 签名密钥
- `ALLOWED_ORIGINS`: 逗号分隔的前端来源

## 说明

- 当前版本把“多 Agent / GraphRAG / Neo4j 增量写入”做成可扩展 scaffold，优先保证首版主链路可运行。
- 若要切换到企业 SSO / LDAP，可在认证服务层扩展，而无需调整前端路由契约。
