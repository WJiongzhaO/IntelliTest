# IntelliTest 项目结构 - 黑盒测试模块

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
│   │   │       ├── base.py                     🆕 生成器基类
│   │   │       ├── equivalence_partitioning.py 🆕 EP 实现
│   │   │       ├── boundary_value_analysis.py  🆕 BVA 实现
│   │   │       ├── decision_table.py           🆕 DT 实现
│   │   │       ├── coverage_manager.py         🆕 覆盖项管理
│   │   │       ├── engine.py                   🆕 主引擎
│   │   │       ├── README.md                   📄 技术文档
│   │   │       └── QUICKSTART.md               📄 快速开始指南
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py                       ✨ [已更新] 注册 blackbox 路由
│   │   │   └── blackbox.py                     🆕 黑盒测试 API 端点
│   │   │
│   │   ├── main.py
│   │   ├── config.py
│   │   └── ...
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   └── test_blackbox_generator.py      🆕 单元测试 (15个)
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
├── docs/
│   └── blackbox_testing_principles.md          📄 技术原理说明（答辩用）
│
├── scripts/
├── prompts/
├── docker-compose.yml
├── README.md
├── IntelliTest项目规划文档.md
└── DELIVERABLES_MEMBER_C.md                    📄 交付清单（本文件索引）
```

## 🎨 图例说明

- 🆕 **新建文件** - 本次开发新增的文件
- ✨ **已更新文件** - 在原有基础上扩展的文件
- 📄 **文档文件** - 技术文档和说明

## 📊 统计信息

### 代码文件
- **新建 Python 文件**: 7 个
- **更新 Python 文件**: 2 个
- **新建 TypeScript 文件**: 0 个（更新现有文件）
- **更新 TypeScript 文件**: 2 个

### 测试文件
- **单元测试**: 1 个文件（15 个测试用例）

### 文档文件
- **技术文档**: 3 个 Markdown 文件
- **总字数**: ~8000 字

### API 端点
- **新增端点**: 7 个
  - GET `/blackbox/techniques`
  - POST `/blackbox/generate/all`
  - POST `/blackbox/generate/{technique}`
  - POST `/blackbox/generate/with-coverage`
  - POST `/blackbox/coverage/identify`
  - POST `/blackbox/coverage/select-techniques`
  - GET `/blackbox/coverage/report-template`

## 🔗 依赖关系图

```
┌─────────────────────────────────────────┐
│         StructuredRequirement           │
│         (app/models/requirement.py)     │
└──────────────┬──────────────────────────┘
               │ 输入
               ▼
┌─────────────────────────────────────────┐
│      BlackBoxTestGenerator              │
│      (engine.py)                        │
│  ┌───────────────────────────────────┐  │
│  │  CoverageManager                  │  │
│  │  - identify_coverage_items()      │  │
│  │  - select_techniques()            │  │
│  │  - generate_report()              │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  EquivalencePartitioningGen.      │  │
│  │  - generate() → EP Test Cases     │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  BoundaryValueAnalysisGen.        │  │
│  │  - generate() → BVA Test Cases    │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  DecisionTableGenerator           │  │
│  │  - generate() → DT Test Cases     │  │
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
- [生成器基类](../backend/app/engines/blackbox_generator/base.py)
- [EP 实现](../backend/app/engines/blackbox_generator/equivalence_partitioning.py)
- [BVA 实现](../backend/app/engines/blackbox_generator/boundary_value_analysis.py)
- [DT 实现](../backend/app/engines/blackbox_generator/decision_table.py)
- [覆盖管理器](../backend/app/engines/blackbox_generator/coverage_manager.py)
- [主引擎](../backend/app/engines/blackbox_generator/engine.py)

### API 接口
- [API 路由](../backend/app/api/blackbox.py)
- [数据模型](../backend/app/models/test_case.py)

### 前端集成
- [TypeScript 类型](../frontend/src/types/models.ts)
- [API 客户端](../frontend/src/api/index.ts)

### 测试与示例
- [单元测试](../backend/tests/unit/test_blackbox_generator.py)
- [演示脚本](../backend/examples/blackbox_demo.py)

### 文档
- [技术文档](../backend/app/engines/blackbox_generator/README.md)
- [快速开始](../backend/app/engines/blackbox_generator/QUICKSTART.md)
- [原理说明](./blackbox_testing_principles.md)
- [交付清单](./DELIVERABLES_MEMBER_C.md)

---

**最后更新**: 2026-05-18  
**版本**: v1.0.0
