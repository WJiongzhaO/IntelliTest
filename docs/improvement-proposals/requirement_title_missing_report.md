# 需求标题字段实现说明与适配记录

## 1. 背景

早期 IntelliTest 的需求管理模块只有后端生成的 `id` 和完整需求正文 `raw_text`，没有独立的需求名称字段。前端在需求列表、风险分析、黑盒测试、综合设计、白盒建模和审查导出等页面只能显示短 id，演示和验收时不够直观。

本次修改已在后端正式增加需求标题字段 `title`，用于保存用户可读的需求名称，并同步适配前端展示、风险信息和导出结果。

## 2. 当前需求字段

需求响应对象当前包含以下字段：

- `id`：后端生成的稳定需求标识。
- `title`：需求标题或需求名称，面向用户展示，可为空。
- `raw_text`：完整需求正文。
- `source_type`：需求来源，例如 `text`、`form`、`csv`。
- `input_fields`：结构化后的输入字段。
- `data_ranges`：结构化后的数据范围或约束。
- `conditions`：结构化后的触发条件。
- `expected_actions`：结构化后的期望系统动作。
- `is_structured`：是否已经完成结构化。
- `risk_impact`：风险影响程度。
- `risk_likelihood`：风险发生可能性。
- `risk_score`：风险分数。
- `priority`：风险优先级。
- `risk_impact_rationale`：风险影响评分理由。
- `risk_likelihood_rationale`：风险可能性评分理由。
- `created_at`：创建时间。
- `updated_at`：更新时间。

其中 `title` 是新增字段，`id` 仍然作为系统内部稳定标识，前端展示时优先使用 `title`，没有标题时回退到 `id`。

## 3. 后端修改范围

### 3.1 数据库模型

`backend/app/models/db_models.py` 中的 `RequirementModel` 已新增：

```python
title: Mapped[str] = mapped_column(String(255), nullable=True)
```

为兼容已有 SQLite 数据，应用启动时会检查 `requirements` 表是否存在 `title` 列；旧库缺少该列时自动执行迁移添加 nullable 字段。

### 3.2 Pydantic 模型

`backend/app/models/requirement.py` 中的 `StructuredRequirement` 已新增：

```python
title: Optional[str] = Field(default=None, description="Human-readable requirement title")
```

`backend/app/api/requirements.py` 中的 `RequirementResponse`、`TextInputRequest`、`FormEntry`、`RequirementUpdate` 也已同步支持 `title`。

### 3.3 需求创建接口

当前创建入口对 `title` 的支持如下：

- `POST /api/v1/requirements/text`：请求体支持 `title`；当文本被拆分为多条需求时，会为后续条目追加序号，避免多条需求重名。
- `POST /api/v1/requirements`：表单输入中 `title` 为必填项。
- `POST /api/v1/requirements/upload`：CSV 导入会识别标题列，支持 `title`、`name`、`requirement_title`、`requirement_name`、`需求名`、`需求名称`、`标题`、`名称` 等列名。

### 3.4 需求更新接口

`PUT /api/v1/requirements/{requirement_id}` 已支持更新 `title`，同时保留对 `raw_text`、`input_fields`、`data_ranges`、`conditions`、`expected_actions` 的更新能力。

### 3.5 结构化与风险分析

需求结构化时，后端会把已有 `title` 传入并保留到 `StructuredRequirement`。风险分析响应 `RiskAssessment` 新增 `requirement_title`，用于让风险结果能直接显示可读需求名称。

## 4. 导出适配

FR 6.0 导出服务已同步支持需求标题：

- CSV 和 Excel 的测试用例导出中新增 `requirement_title` 字段。
- Excel 的 `Requirements` 工作表中包含 `title` 字段。
- Excel 的 `Coverage` 工作表中新增 `requirement_title` 字段。
- JSON 导出中，`requirements` 使用 `StructuredRequirement` 的完整结构，因此包含 `title`。

这样导出文件既保留 `requirement_id` 的稳定追溯能力，也提供 `requirement_title` 给人工审查和课程展示使用。

## 5. 前端适配

前端已增加统一展示逻辑：优先显示需求 `title`，为空时回退到 `id`。已适配位置包括：

- 需求输入页的必填需求名输入。
- 需求列表的需求名列。
- 风险分析页面。
- 黑盒测试需求选择。
- 综合设计需求选择。
- 白盒建模需求选择。
- 审查导出中的需求追溯和覆盖项追溯。

## 6. 兼容策略

`title` 设计为可空字段，避免破坏历史数据和已有接口调用。统一展示规则为：

```text
display_name = title if title exists else id
```

因此旧数据仍可正常使用，新数据则可以保存和展示更友好的需求名称。

## 7. 当前结论

需求标题字段缺失问题已完成后端持久化、接口响应、输入解析、风险结果、导出结果和前端展示适配。后续如果继续扩展测试套件持久化，也应在测试套件与覆盖项相关表中保留 `requirement_id`，并在导出或展示层通过需求表补充 `requirement_title`。
