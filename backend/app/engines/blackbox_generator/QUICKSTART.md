# 黑盒测试模块快速开始指南

## 1. 环境准备

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

确保已安装以下关键依赖：
- `fastapi` - Web 框架
- `pydantic` - 数据验证
- `pytest` - 测试框架

## 2. 运行单元测试

验证所有组件是否正常工作：

```bash
cd backend
pytest tests/unit/test_blackbox_generator.py -v
```

**预期输出**：
```
tests/unit/test_blackbox_generator.py::TestEquivalencePartitioning::test_generate_ep_tests PASSED
tests/unit/test_blackbox_generator.py::TestBoundaryValueAnalysis::test_generate_bva_tests PASSED
tests/unit/test_blackbox_generator.py::TestDecisionTable::test_generate_dt_tests PASSED
tests/unit/test_blackbox_generator.py::TestBlackBoxEngine::test_generate_all_techniques PASSED
...
========================= 15 passed in 0.5s =========================
```

## 3. 运行演示脚本

查看完整的生成流程：

```bash
cd backend
python examples/blackbox_demo.py
```

**预期输出**：
```
================================================================================
IntelliTest - Black-Box Test Generation Demo
================================================================================

1. Creating sample requirement...
   Requirement ID: REQ_USER_REG
   Input Fields: age, email, password, membership_type
   Conditions: 2

2. Initializing BlackBoxTestGenerator...

3. Available Testing Techniques:

   [EP] Equivalence Partitioning
       Divides input data into equivalence classes...
       Best for: Testing input validation and data range handling

   [BVA] Boundary Value Analysis
       Tests values at, just below, and just above boundaries...
       Best for: Testing numerical ranges and boundary conditions

   [DT] Decision Table Testing
       Tests all combinations of conditions...
       Best for: Testing complex business rules and conditional logic

4. Generating test cases with all techniques...

   Generated 25 test cases
   Identified 8 coverage items

5. Coverage Report:
   Total Coverage Items: 8
   Covered Items: 8
   Uncovered Items: 0
   Coverage Percentage: 100.0%

   Technique Usage:
     - EP: 8 test cases
     - BVA: 12 test cases
     - DT: 5 test cases

...

7. Exporting Results:
   Results exported to: blackbox_test_results.json
   File size: 15234 bytes

================================================================================
Demo completed successfully!
================================================================================
```

## 4. 启动后端 API 服务

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

服务将在 `http://localhost:8000` 启动。

### 访问 API 文档

打开浏览器访问：`http://localhost:8000/docs`

你将看到 Swagger UI 界面，可以交互式测试所有 API 端点。

## 5. API 调用示例

### 使用 cURL

#### 获取可用技术信息

```bash
curl http://localhost:8000/api/v1/blackbox/techniques
```

#### 生成所有技术的测试用例

```bash
curl -X POST "http://localhost:8000/api/v1/blackbox/generate/all" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "REQ001",
    "raw_text": "User age must be between 18 and 120",
    "input_fields": ["age"],
    "data_ranges": ["Age between 18 and 120"],
    "conditions": ["If age >= 18"],
    "expected_actions": ["Register user"]
  }'
```

#### 生成带覆盖追踪的测试用例（推荐）

```bash
curl -X POST "http://localhost:8000/api/v1/blackbox/generate/with-coverage" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": {
      "id": "REQ001",
      "raw_text": "User registration with age validation",
      "input_fields": ["age", "email"],
      "data_ranges": ["Age between 18 and 120"],
      "conditions": ["If age >= 65", "If email is valid"],
      "expected_actions": ["Create account", "Send email"]
    },
    "selected_techniques": ["EP", "BVA", "DT"]
  }'
```

### 使用 Python requests

```python
import requests
import json

# API 基础 URL
BASE_URL = "http://localhost:8000/api/v1"

# 准备需求数据
requirement = {
    "id": "REQ001",
    "raw_text": "User age must be between 18 and 120",
    "input_fields": ["age"],
    "data_ranges": ["Age between 18 and 120"],
    "conditions": ["If age >= 18"],
    "expected_actions": ["Register user"]
}

# 调用 API
response = requests.post(
    f"{BASE_URL}/blackbox/generate/with-coverage",
    json={"requirement": requirement}
)

# 解析结果
result = response.json()
print(f"Generated {len(result['test_cases'])} test cases")
print(f"Coverage: {result['coverage_report']['coverage_percentage']}%")
```

## 6. 前端集成（可选）

如果你要开发前端界面：

### 安装前端依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:3000` 启动。

### 调用 API

在 React 组件中使用：

```tsx
import { generateWithCoverage } from '@/api';

const handleGenerate = async () => {
  const result = await generateWithCoverage(requirement);
  console.log('Test cases:', result.data.test_cases);
  console.log('Coverage:', result.data.coverage_report);
};
```

## 7. 常见问题

### Q1: 测试失败，提示导入错误

**解决方案**：确保在 `backend` 目录下运行，并且已安装所有依赖。

```bash
cd backend
pip install -r requirements.txt
```

### Q2: API 返回 404 错误

**解决方案**：检查 URL 是否正确，应为 `/api/v1/blackbox/...`

### Q3: 生成的测试用例数量不符合预期

**可能原因**：
- 需求中的条件数量为 0，导致 DT 无法生成
- 数据范围格式不匹配正则表达式

**解决方案**：检查 `StructuredRequirement` 的字段是否正确填充。

### Q4: 如何自定义边界值？

当前实现自动从文本中提取边界。如需手动指定，可修改 `boundary_value_analysis.py` 中的 `_extract_boundaries` 方法。

## 8. 性能基准

在普通笔记本电脑上（Intel i7, 16GB RAM）：

| 操作 | 耗时 |
|------|------|
| EP 生成（3 个字段） | < 10ms |
| BVA 生成（2 个范围） | < 15ms |
| DT 生成（3 个条件） | < 20ms |
| 完整生成（所有技术） | < 50ms |
| **总计** | **< 100ms** |

✅ **满足 FR 1.4 性能要求（≤ 2 秒）**

## 9. 下一步

- 📖 阅读 [`README.md`](../backend/app/engines/blackbox_generator/README.md) 了解详细技术文档
- 📚 阅读 [`blackbox_testing_principles.md`](../../docs/blackbox_testing_principles.md) 了解技术原理
- 🧪 编写自己的测试用例，验证不同场景
- 🔧 扩展新的黑盒测试技术（如状态转换测试）

## 10. 支持

如有问题，请：
1. 查看单元测试作为使用示例
2. 运行演示脚本观察输出
3. 访问 Swagger UI (`/docs`) 探索 API

---

**祝使用愉快！** 🎉
