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
│   │   │   ├── blackbox_generator/  # FR 3.0 黑盒测试生成 (EP/BVA/DT) 🆕 v2.0 LLM集成
│   │   │   ├── whitebox_modeler/    # FR 4.0 白盒建模
│   │   │   ├── oracle_synthesizer/  # FR 5.0 测试预言合成
│   │   │   ├── export_service/      # FR 6.0 输出导出
│   │   │   └── suite_optimizer/     # FR 7.0 测试套件优化
│   │   ├── services/            # 服务层
│   │   │   ├── llm_client.py        # 🆕 LLM客户端（多提供商支持）
│   │   │   └── ...
│   │   ├── prompts/             # LLM Prompt 模板加载器
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
├── prompts/                     # 🆕 共享 Prompt 模板 (版本控制)
│   └── blackbox_test_design.txt # 黑盒测试设计专用Prompt
├── docs/                        # 项目文档及交付物
├── scripts/                     # 构建/部署脚本
├── docker-compose.yml           # 容器编排
├── .env.example                 # 环境变量模板
└── .gitignore
```

### 🆕 v2.0 架构更新说明

**黑盒测试模块（FR 3.0）**已升级为 **LLM优先 + 规则兜底** 的混合架构：

- ✅ **LLM驱动**：深度理解自然语言需求，智能生成高质量测试用例
- ✅ **多提供商支持**：Claude / OpenAI / DeepSeek 自由切换
- ✅ **自动降级**：LLM失败时自动切换到规则引擎，确保功能可用性
- ✅ **Prompt管理**：统一模板化管理，便于团队协作和优化

详细架构说明请参考：
- [黑盒测试模块技术文档](backend/app/engines/blackbox_generator/README.md)
- [黑盒测试原理说明](docs/blackbox_testing_principles.md)
- [项目结构文档](PROJECT_STRUCTURE_BLACKBOX.md)

## 技术栈

| 层 | 技术 |
|---|---|
| **前端** | React 18, TypeScript, Ant Design 5.x, Zustand, Vite |
| **后端** | Python 3.12, FastAPI, Pydantic, SQLAlchemy |
| **AI** | Claude API / OpenAI API / DeepSeek API, 结构化 Prompt Engineering, LLM-First架构 |
| **数据处理** | Pandas, openpyxl |
| **部署** | Docker + Docker Compose |

### 🆕 AI集成特性（v2.0）

- **多LLM提供商支持**：Anthropic Claude / OpenAI GPT / DeepSeek
- **智能容错机制**：LLM失败自动降级到规则引擎
- **Prompt工程化**：统一模板管理，版本控制
- **结构化输出**：强制JSON格式，便于程序解析

## 快速开始

### 环境要求

- Python 3.11+ （推荐 3.11）
- Node.js 20+
- Docker（可选）

### 后端启动

```bash
cd backend

# 1. 创建虚拟环境（仅首次）
python -m venv venv

# 2. 激活虚拟环境
#    Windows:
venv\Scripts\activate
#    Linux / macOS:
source venv/bin/activate

# 3. 安装依赖（仅首次或 requirements.txt 变更后）
pip install -r requirements.txt

# 4. 配置环境变量
#    a) 复制模板文件
copy ..\.env.example .env     # Windows（在 backend 目录下）
# cp ../.env.example .env     # Linux / macOS

#    b) 编辑 .env 文件，填入 LLM API Key（必需！）
#       - llm_provider=anthropic
#       - anthropic_api_key=sk-ant-api03-...
#       详见下方 "LLM 配置说明"

# 5. 启动服务
uvicorn app.main:app --reload --port 8000
```

API 文档自动生成于 <http://localhost:8000/docs>

#### ⚠️ LLM 配置说明（重要！）

黑盒测试模块的LLM功能**必须配置API密钥**，否则将自动降级到规则引擎。

**配置步骤**：

1. 在项目根目录创建 `.env` 文件（参考 `.env.example`）
2. 配置至少一个LLM提供商的API Key：

```bash
# 选择LLM提供商: anthropic, openai, deepseek
llm_provider=anthropic

# Anthropic Claude API（推荐，质量最佳）
anthropic_api_key=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# 或 OpenAI API（备选）
# openai_api_key=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# 或 DeepSeek API（备选，国内网络友好）
# deepseek_api_key=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# deepseek_base_url=https://api.deepseek.com/v1

# LLM模型配置
llm_model=claude-sonnet-4-6
llm_temperature_structured=0.0
llm_max_retries=3
```

3. 重启后端服务使配置生效

**验证配置**：

- ✅ 正常：后端日志显示 `LLM blackbox generated req=REQ_XXX cases=14 techniques=['EP', 'BVA', 'DT']`
- ❌ 异常：后端日志显示 `LLM not available, using rule-based generation`

**详细说明**：请参考 [黑盒测试模块技术文档](backend/app/engines/blackbox_generator/README.md) 的"环境配置"章节。

### 前端启动

```bash
cd frontend
npm install                    # 仅首次
npm run dev                    # http://localhost:3000
```

### Docker 一键启动

```bash
# 环境变量统一放在 backend/.env（与 docker-compose 一致）
cp .env.example backend/.env   # 或使用团队提供的 backend/.env
docker-compose up --build
```

若拉取 `docker.io` 超时，`docker-compose.yml` 已配置 DaoCloud 镜像前缀；也可先执行 `docker pull docker.m.daocloud.io/library/node:20-alpine`。

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

## 成员 D 文档

- [docs/白盒建模方法说明.md](docs/白盒建模方法说明.md)
- [docs/详细测试设计与执行文档.md](docs/详细测试设计与执行文档.md)
- [scripts/target_app_tests/](scripts/target_app_tests/) — PyTest 骨架

## API 端点摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/blackbox/generate/all` | 黑盒 EP+BVA+DT 全量生成（成员 C） |
| POST | `/api/v1/blackbox/generate/with-coverage` | 黑盒生成 + 覆盖项报告 |
| POST | `/api/v1/whitebox/model` | 白盒建模：状态图 + 覆盖序列 + 用例（成员 D） |
| PUT | `/api/v1/whitebox/model/{id}` | 人工修订模型后重算覆盖 |
| POST | `/api/v1/oracle/synthesize` | CoT 合成测试预言 |
| PUT | `/api/v1/oracle/{id}/review` | 确认/驳回预言（`modified_by_user`） |
| POST | `/api/v1/test-design/combined` | 黑盒+白盒合并流水线 |

完整契约见 <http://localhost:8000/docs>。

## 交付物

1. AutoTestDesign 工具 (源代码 + README + 演示)
2. 风险分析报告
3. 测试计划
4. 详细测试设计与执行文档
