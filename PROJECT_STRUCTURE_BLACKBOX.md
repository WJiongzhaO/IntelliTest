# IntelliTest 项目结构 - 黑盒测试模块

> **版本**: v2.0.0 | **最后更新**: 2026-05-31  
> **架构**: LLM优先 + 规则引擎兜底（LLM-First with Rule-Based Fallback）

## 📁 完整文件清单

```
IntelliTest/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── requirement.py
│   │   │   └── test_case.py                    ✨ [已扩展] 添加 BlackBoxTechnique, CoverageItem
│   │   │
│   │   ├── engines/
│   │   │   ├── __init__.py
│   │   │   └── blackbox_generator/             🆕 [新建模块]
│   │   │       ├── __init__.py                 ✨ 导出所有组件
│   │   │       ├── engine.py                   🎯 主引擎编排器（LLM+规则调度）
│   │   │       ├── llm_generator.py            🆕 LLM驱动生成器
│   │   │       ├── schema.py                   🆕 LLM输出验证与解析
│   │   │       ├── base.py                     生成器基类
│   │   │       ├── equivalence_partitioning.py 规则引擎：EP实现
│   │   │       ├── boundary_value_analysis.py  规则引擎：BVA实现
│   │   │       ├── decision_table.py           规则引擎：DT实现
│   │   │       ├── coverage_manager.py         覆盖项管理
│   │   │       └── README.md                   📄 技术文档
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py                       ✨ [已更新] 注册 blackbox 路由
│   │   │   └── blackbox.py                     🆕 黑盒测试 API 端点
│   │   │
│   │   ├── services/
│   │   │   ├── llm_client.py                   🆕 LLM客户端（多提供商支持）
│   │   │   └── llm_types.py                    🆕 LLM接口类型定义
│   │   │
│   │   ├── prompts/
│   │   │   └── loader.py                       🆕 Prompt模板加载器
│   │   │
│   │   ├── main.py
│   │   ├── config.py
│   │   └── ...
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   ├── test_blackbox_generator.py      🆕 单元测试 (15个)
│   │   │   └── test_blackbox_llm.py            🆕 LLM集成测试 (8个)
│   │   ├── integration/
│   │   └── e2e/
│   │
│   ├── examples/
│   │   └── blackbox_demo.py                    🆕 演示脚本
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── types/
│   │   │   ├── index.ts
│   │   │   └── models.ts                       ✨ [已扩展] 添加黑盒相关类型
│   │   │
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   └── index.ts                        ✨ [已扩展] 添加黑盒 API 方法
│   │   │
│   │   ├── components/
│   │   ├── pages/
│   │   ├── stores/
│   │   └── ...
│   │
│   └── package.json
│
├── prompts/
│   └── blackbox_test_design.txt                🆕 LLM Prompt模板（结构化格式）
│
├── docs/
│   └── blackbox_testing_principles.md          📄 技术原理说明（答辩用）
│
├── scripts/
├── docker-compose.yml
├── README.md
└── DELIVERABLES_MEMBER_C.md                    📄 交付清单（本文件索引）
```

## 🎨 图例说明

- 🎯 **核心组件** - 架构关键入口
- 🆕 **v2.0新增** - LLM集成相关组件
- ✨ **已更新文件** - 在原有基础上扩展的文件
- 📄 **文档文件** - 技术文档和说明

## 🏗️ 架构演进

### v1.0 → v2.0 关键变化

| 维度 | v1.0（旧版） | v2.0（新版） |
|------|-------------|-------------|
| **架构模式** | 纯规则引擎 | LLM优先 + 规则兜底 |
| **需求理解** | 正则表达式匹配 | LLM深度语义理解 |
| **测试质量** | 中等（模板化预期结果） | 高（精准预期结果） |
| **容错机制** | 无 | LLM失败自动降级到规则引擎 |
| **Prompt管理** | 无 | 统一Prompt模板（`prompts/`目录） |
| **多提供商支持** | 无 | Claude/OpenAI/DeepSeek |

## 📊 统计信息

### 代码文件
- **新建 Python 文件**: 10 个（含LLM集成组件）
- **更新 Python 文件**: 2 个
- **新建 TypeScript 文件**: 0 个（更新现有文件）
- **更新 TypeScript 文件**: 2 个

### 测试文件
- **单元测试**: 2 个文件（23 个测试用例）
  - `test_blackbox_generator.py`: 15个（规则引擎）
  - `test_blackbox_llm.py`: 8个（LLM集成）

### 文档文件
- **技术文档**: 4 个 Markdown 文件
- **总字数**: ~15000 字（含LLM架构说明）

### API 端点
- **新增端点**: 7 个
  - GET `/blackbox/techniques`
  - POST `/blackbox/generate/all`
  - POST `/blackbox/generate/{technique}`
  - POST `/blackbox/generate/with-coverage`
  - POST `/blackbox/coverage/identify`
  - POST `/blackbox/coverage/select-techniques`
  - GET `/blackbox/coverage/report-template`

## 🔗 依赖关系图（v2.0 新架构）

```
┌─────────────────────────────────────────┐
│         StructuredRequirement           │
│         (app/models/requirement.py)     │
└──────────────┬──────────────────────────┘
               │ 输入
               ▼
┌─────────────────────────────────────────┐
│      BlackBoxTestGenerator              │
│      (engine.py) - 主引擎编排器          │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  第一优先级：LLMBlackBoxGenerator │  │
│  │  - load_prompt_template()         │  │
│  │  - build_user_prompt()            │  │
│  │  - llm.complete_json()            │  │
│  │  - validate & parse output        │  │
│  │  ↓ 失败时自动降级                   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  第二优先级：规则引擎（降级方案）    │  │
│  │  ├─ EquivalencePartitioningGen.   │  │
│  │  ├─ BoundaryValueAnalysisGen.     │  │
│  │  └─ DecisionTableGenerator        │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  CoverageManager                  │  │
│  │  - identify_coverage_items()      │  │
│  │  - merge_coverage_items()         │  │
│  │  - generate_report()              │  │
│  └───────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │ 输出
               ▼
┌─────────────────────────────────────────┐
│         list[TestCase]                  │
│         + CoverageReport                │
│         (app/models/test_case.py)       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         API Router                      │
│         (app/api/blackbox.py)           │
│         - 7 RESTful endpoints           │
└──────────────┬──────────────────────────┘
               │ HTTP/JSON
               ▼
┌─────────────────────────────────────────┐
│         Frontend                        │
│         (TypeScript + React)            │
│         - Type definitions              │
│         - API client methods            │
└─────────────────────────────────────────┘
```

## 🚀 快速导航

### 核心实现
- [主引擎编排器](../backend/app/engines/blackbox_generator/engine.py) - LLM+规则调度
- [LLM生成器](../backend/app/engines/blackbox_generator/llm_generator.py) - LLM驱动测试设计
- [Prompt加载器](../backend/app/prompts/loader.py) - 模板化管理
- [LLM客户端](../backend/app/services/llm_client.py) - 多提供商支持
- [规则引擎：EP](../backend/app/engines/blackbox_generator/equivalence_partitioning.py)
- [规则引擎：BVA](../backend/app/engines/blackbox_generator/boundary_value_analysis.py)
- [规则引擎：DT](../backend/app/engines/blackbox_generator/decision_table.py)
- [覆盖管理器](../backend/app/engines/blackbox_generator/coverage_manager.py)

### API 接口
- [API 路由](../backend/app/api/blackbox.py)
- [数据模型](../backend/app/models/test_case.py)

### 前端集成
- [TypeScript 类型](../frontend/src/types/models.ts)
- [API 客户端](../frontend/src/api/index.ts)

### 测试与示例
- [规则引擎测试](../backend/tests/unit/test_blackbox_generator.py)
- [LLM集成测试](../backend/tests/unit/test_blackbox_llm.py)
- [演示脚本](../backend/examples/blackbox_demo.py)

### 文档
- [模块技术文档](../backend/app/engines/blackbox_generator/README.md) - **详细架构说明**
- [原理说明](./docs/blackbox_testing_principles.md)
- [交付清单](./DELIVERABLES_MEMBER_C.md)

---

**最后更新**: 2026-05-31  
**版本**: v2.0.0（LLM集成版）
