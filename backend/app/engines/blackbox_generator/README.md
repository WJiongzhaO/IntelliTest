# 黑盒测试设计模块技术文档

## 概述

本模块实现了符合 **ISO 29119-4** 标准的三种核心黑盒测试技术：
- **等价划分（Equivalence Partitioning, EP）**
- **边界值分析（Boundary Value Analysis, BVA）**
- **决策表测试（Decision Table Testing, DT）**

## 架构设计

### 核心组件

```
backend/app/engines/blackbox_generator/
├── __init__.py                    # 模块导出接口
├── base.py                        # 生成器基类（抽象接口）
├── equivalence_partitioning.py    # EP 实现
├── boundary_value_analysis.py     # BVA 实现
├── decision_table.py              # DT 实现
├── coverage_manager.py            # 覆盖项管理器
└── engine.py                      # 主引擎（编排器）
```

### 设计模式

1. **策略模式（Strategy Pattern）**：`BaseBlackBoxGenerator` 定义统一接口，三种技术分别实现
2. **工厂模式（Factory Pattern）**：`BlackBoxTestGenerator` 根据技术类型选择对应生成器
3. **模板方法模式（Template Method）**：基类提供通用方法（如 ID 生成），子类实现特定逻辑

## 技术实现细节

### 1. 等价划分（EP）

**原理**：将输入域划分为若干等价类，从每个类中选取代表性值进行测试。

**实现要点**：
- 自动识别有效/无效等价类
- 从需求描述中提取数据范围
- 为每个等价类生成独立测试用例

**示例输出**：
```python
TestCase(
    id="REQ001_EP_001",
    title="EP Test: age - Valid equivalence class",
    test_data="50",  # 典型有效值
    expected_result="System should accept the input and process normally",
    technique=BlackBoxTechnique.EP,
    priority=Priority.MEDIUM
)
```

### 2. 边界值分析（BVA）

**原理**：错误常发生在边界处，因此测试边界值及其邻域。

**实现要点**：
- 使用正则表达式提取数值边界（如 "between 18 and 120"）
- 为每个边界生成 6 个测试用例：
  - 最小值 -1（无效）
  - 最小值（有效）
  - 最小值 +1（有效）
  - 最大值 -1（有效）
  - 最大值（有效）
  - 最大值 +1（无效）

**示例输出**：
```python
TestCase(
    id="REQ001_BVA_001",
    title="BVA Test: age - Below minimum boundary (17)",
    test_data="17",
    expected_result="System should reject the value 17 with appropriate error message",
    technique=BlackBoxTechnique.BVA,
    priority=Priority.HIGH
)
```

### 3. 决策表测试（DT）

**原理**：通过条件组合生成所有可能的业务规则，确保逻辑完整性。

**实现要点**：
- 从需求中提取布尔条件和多值条件
- 使用笛卡尔积生成所有规则组合
- 为每条规则生成测试用例

**示例**：
对于 2 个布尔条件，生成 2² = 4 条规则：
- C1=True, C2=True
- C1=True, C2=False
- C1=False, C2=True
- C1=False, C2=False

## 覆盖项管理

### CoverageItem 模型

```python
class CoverageItem(BaseModel):
    id: str                              # 唯一标识符
    requirement_id: str                  # 关联需求
    description: str                     # 覆盖项描述
    item_type: str                       # 类型：input_field/boundary/condition
    selected_techniques: list[Technique] # 选定的测试技术
    covered_by_test_cases: list[str]     # 覆盖该项目的测试用例 ID
```

### 覆盖率计算

```python
coverage_percentage = (covered_items / total_items) * 100
```

### 覆盖报告

包含以下指标：
- 总覆盖项数
- 已覆盖/未覆盖项数
- 覆盖率百分比
- 按类型分布
- 按技术使用情况
- 未覆盖项详情列表

## API 接口

### 1. 获取可用技术信息

```http
GET /api/v1/blackbox/techniques
```

**响应**：
```json
{
  "EP": {
    "name": "Equivalence Partitioning",
    "description": "...",
    "standard": "ISO 29119-4",
    "best_for": "Testing input validation"
  },
  "BVA": { ... },
  "DT": { ... }
}
```

### 2. 生成所有技术的测试用例

```http
POST /api/v1/blackbox/generate/all
Content-Type: application/json

{
  "id": "REQ001",
  "input_fields": ["age", "email"],
  "data_ranges": ["Age must be between 18 and 120"],
  "conditions": ["If age >= 18"],
  "expected_actions": ["Register user"]
}
```

**响应**：`list[TestCase]`

### 3. 生成特定技术的测试用例

```http
POST /api/v1/blackbox/generate/{technique}
```

其中 `technique` 为 `EP`、`BVA` 或 `DT`。

### 4. 带覆盖追踪的生成（推荐）

```http
POST /api/v1/blackbox/generate/with-coverage
```

**响应**：
```json
{
  "coverage_items": [...],
  "test_cases": [...],
  "coverage_report": {
    "total_coverage_items": 10,
    "covered_items": 8,
    "uncovered_items": 2,
    "coverage_percentage": 80.0,
    "type_distribution": {...},
    "technique_usage": {"EP": 5, "BVA": 3, "DT": 2},
    "uncovered_item_details": [...]
  }
}
```

### 5. 识别覆盖项

```http
POST /api/v1/blackbox/coverage/identify
```

### 6. 为覆盖项选择技术

```http
POST /api/v1/blackbox/coverage/select-techniques
```

## 前端集成

### TypeScript 类型定义

已在 `frontend/src/types/models.ts` 中定义：

```typescript
export type BlackBoxTechnique = 'EP' | 'BVA' | 'DT';

export interface CoverageItem {
  id: string;
  requirement_id: string;
  description: string;
  item_type: string;
  selected_techniques: BlackBoxTechnique[];
  covered_by_test_cases: string[];
}

export interface CoverageReport {
  total_coverage_items: number;
  covered_items: number;
  uncovered_items: number;
  coverage_percentage: number;
  type_distribution: Record<string, { total: number; covered: number }>;
  technique_usage: Record<string, number>;
  uncovered_item_details: Array<{
    id: string;
    description: string;
    type: string;
  }>;
}
```

### API 客户端方法

已在 `frontend/src/api/index.ts` 中提供：

```typescript
import {
  getTechniques,
  generateAllTechniques,
  generateSpecificTechnique,
  generateWithCoverage,
  identifyCoverageItems,
  selectTechniquesForCoverageItem,
  getCoverageReportTemplate,
} from '@/api';
```

## 使用示例

### Python 后端调用

```python
from app.engines.blackbox_generator import BlackBoxTestGenerator
from app.models.requirement import StructuredRequirement

# 1. 创建结构化需求
requirement = StructuredRequirement(
    id="REQ001",
    raw_text="User registration with age 18-120",
    input_fields=["age", "email"],
    data_ranges=["Age between 18 and 120"],
    conditions=["If age >= 18"],
    expected_actions=["Register user"]
)

# 2. 初始化引擎
engine = BlackBoxTestGenerator()

# 3. 生成测试用例（带覆盖追踪）
result = engine.generate_with_coverage_tracking(requirement)

# 4. 访问结果
test_cases = result['test_cases']
coverage_report = result['coverage_report']

print(f"Generated {len(test_cases)} test cases")
print(f"Coverage: {coverage_report['coverage_percentage']}%")
```

### 前端 React 组件调用

```tsx
import { generateWithCoverage } from '@/api';
import type { StructuredRequirement, BlackBoxGenerationResult } from '@/types/models';

const BlackBoxTestGenerator: React.FC = () => {
  const [result, setResult] = useState<BlackBoxGenerationResult | null>(null);

  const handleGenerate = async (requirement: StructuredRequirement) => {
    try {
      const response = await generateWithCoverage(requirement);
      setResult(response.data);
    } catch (error) {
      console.error('Generation failed:', error);
    }
  };

  return (
    <div>
      <button onClick={() => handleGenerate(requirement)}>
        Generate Test Cases
      </button>
      
      {result && (
        <div>
          <h3>Coverage Report</h3>
          <p>Coverage: {result.coverage_report.coverage_percentage}%</p>
          <p>Total Test Cases: {result.test_cases.length}</p>
          
          <h4>Test Cases by Technique:</h4>
          <ul>
            {Object.entries(result.coverage_report.technique_usage).map(([tech, count]) => (
              <li key={tech}>{tech}: {count} tests</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

## 测试与验证

### 运行单元测试

```bash
cd backend
pytest tests/unit/test_blackbox_generator.py -v
```

### 测试覆盖场景

1. **EP 测试**：验证等价类识别和测试用例生成
2. **BVA 测试**：验证边界值提取和测试数据准确性
3. **DT 测试**：验证条件组合完整性
4. **覆盖管理**：验证覆盖率计算和报告生成
5. **集成测试**：验证完整工作流

## ISO 29119-4 合规性

本实现严格遵循 ISO 29119-4 标准：

| 标准要求 | 实现方式 |
|---------|---------|
| 等价划分 | 识别有效/无效类，每类至少一个测试用例 |
| 边界值分析 | 测试边界、略低于、略高于边界的值 |
| 决策表 | 覆盖所有条件组合，每条规则一个测试用例 |
| 可追溯性 | 通过 CoverageItem 建立需求-覆盖项-测试用例的映射 |
| 文档化 | 每个测试用例包含标题、步骤、预期结果、技术来源 |

## 扩展性设计

### 添加新的黑盒测试技术

1. 在 `app/models/test_case.py` 中添加新的 `BlackBoxTechnique` 枚举值
2. 创建新的生成器类，继承 `BaseBlackBoxGenerator`
3. 实现 `technique` 属性和 `generate` 方法
4. 在 `BlackBoxTestGenerator.__init__` 中注册新生成器
5. 更新前端类型定义

### 自定义覆盖项类型

修改 `CoverageManager.identify_coverage_items` 方法，添加新的 item_type 识别逻辑。

## 性能优化建议

1. **缓存机制**：对相同需求的生成结果进行缓存
2. **异步处理**：对于大量条件的 DT 生成，使用异步任务队列
3. **规则剪枝**：DT 中对不可能出现的条件组合进行剪枝
4. **并行生成**：三种技术可并行执行

## 已知限制与改进方向

### 当前限制

1. **NLP 解析精度**：依赖简单的字符串匹配，复杂需求可能需要人工干预
2. **数值边界识别**：仅支持整数边界，浮点数需扩展
3. **DT 组合爆炸**：条件过多时测试用例数量呈指数增长

### 改进方向

1. 集成 LLM 提升需求解析能力
2. 支持更复杂的数据类型（日期、枚举等）
3. 实现智能规则剪枝算法
4. 添加测试用例去重和优化

## 总结

本模块提供了完整的黑盒测试设计自动化解决方案，符合 ISO 29119-4 标准，具备：
- ✅ 三种核心技术的完整实现
- ✅ 统一的生成器接口
- ✅ 覆盖项管理和追踪
- ✅ RESTful API 接口
- ✅ 前端 TypeScript 集成
- ✅ 全面的单元测试

为 IntelliTest 项目的 FR 3.0 功能需求提供了坚实的技术基础。
