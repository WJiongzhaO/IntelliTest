# IntelliTest

**AI-Driven AutoTestDesign Tool** — 基于 AI 的自动化测试设计工具，用于软件需求分析、风险评估与系统化测试用例生成。

> Team: **ATCrafters**

---

## 项目架构

```
IntelliTest/
├── backend/                     # Python FastAPI 后端服务
│   ├── app/
│   │   ├── main.py              # FastAPI 应用入口
│   │   ├── config.py            # 配置管理 (pydantic-settings)
│   │   ├── api/                 # API 路由层
│   │   │   └── router.py        # 主路由聚合器
│   │   ├── models/              # Pydantic 数据模型 (TestCase, TestSuite, Requirement)
│   │   ├── engines/             # 各功能引擎模块
│   │   │   ├── input_parser/        # FR 1.0 输入解析
│   │   │   ├── requirement_structurer/  # FR 1.1 需求结构化
│   │   │   ├── risk_analyzer/       # FR 2.0 风险分析
│   │   │   ├── blackbox_generator/  # FR 3.0 黑盒测试生成 (EP/BVA/DT)
│   │   │   ├── whitebox_modeler/    # FR 4.0 白盒建模
│   │   │   ├── oracle_synthesizer/  # FR 5.0 测试预言合成
│   │   │   ├── export_service/      # FR 6.0 输出导出
│   │   │   └── suite_optimizer/     # FR 7.0 测试套件优化
│   │   ├── prompts/             # LLM Prompt 模板
│   │   └── utils/               # 工具函数 (logger 等)
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
├── frontend/                    # React 18 + TypeScript 前端
│   ├── src/
│   │   ├── main.tsx             # 应用入口
│   │   ├── App.tsx              # 根组件 (路由 + 布局)
│   │   ├── api/                 # Axios 客户端及 API 调用封装
│   │   ├── components/          # 可复用组件
│   │   ├── pages/               # 各功能页面
│   │   ├── stores/              # Zustand 状态管理
│   │   ├── types/               # TypeScript 类型定义
│   │   └── utils/               # 前端工具函数
│   └── Dockerfile
├── prompts/                     # 共享 Prompt 模板 (版本控制)
├── docs/                        # 项目文档及交付物
├── scripts/                     # 构建/部署脚本
├── docker-compose.yml           # 容器编排
├── .env.example                 # 环境变量模板
└── .gitignore
```

## 技术栈

| 层 | 技术 |
|---|---|
| **前端** | React 18, TypeScript, Ant Design 5.x, Zustand, Vite |
| **后端** | Python 3.12, FastAPI, Pydantic, SQLAlchemy |
| **AI** | Claude API / OpenAI API, 结构化 Prompt Engineering |
| **数据处理** | Pandas, openpyxl |
| **部署** | Docker + Docker Compose |

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 20+
- Docker (可选)

### 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env    # 编辑 .env 填入 API Key
uvicorn app.main:app --reload --port 8000
```

API 文档自动生成于 <http://localhost:8000/docs>

### 前端启动

```bash
cd frontend
npm install
cp ../.env.example .env    # 编辑 .env 配置
npm run dev                 # http://localhost:3000
```

### Docker 一键启动

```bash
cp .env.example .env       # 编辑 .env 填入 API Key
docker-compose up --build
```

## 功能模块映射 (FRs)

| FR | 功能 | 后端引擎 |
|---|---|---|
| FR 1.0 | 需求输入/解析 | `engines/input_parser/` |
| FR 1.1 | 需求结构化 | `engines/requirement_structurer/` |
| FR 2.0 | 风险分析 | `engines/risk_analyzer/` |
| FR 3.0 | 黑盒测试设计 | `engines/blackbox_generator/` |
| FR 4.0 | 白盒测试建模 | `engines/whitebox_modeler/` |
| FR 5.0 | 测试预言生成 | `engines/oracle_synthesizer/` |
| FR 6.0 | 输出/导出 | `engines/export_service/` |
| FR 7.0 | 测试套件优化 | `engines/suite_optimizer/` |

## 开发规范

- **Commit**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- **分支**: `main` (稳定) → `dev` (集成) → `feature/<模块名>`
- **Python**: PEP 8, Black (100 chars), 类型注解, Google docstring
- **TypeScript**: ESLint + Prettier, strict mode, 函数组件 + Hooks
- **API Key**: 仅通过 `.env` 配置，禁止硬编码和提交

## 交付物

1. AutoTestDesign 工具 (源代码 + README + 演示)
2. 风险分析报告
3. 测试计划
4. 详细测试设计与执行文档
