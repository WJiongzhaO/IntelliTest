# 成员 E - FR 6.0 输出与导出服务说明

## 目标

FR 6.0 要求 IntelliTest 能将测试工件以结构化标准格式导出，便于导入测试管理工具或作为课程交付材料。当前实现支持：

- JSON：保留完整层级结构，适合归档和二次处理。
- CSV：以测试用例为主表，适合导入表格或测试管理工具。
- Excel：包含 Summary、Test Cases、Requirements、Coverage 多个工作表，适合人工审查和演示。

## 文件位置

- 后端导出引擎：`backend/app/engines/export_service/exporter.py`
- 后端 API 路由：`backend/app/api/export.py`
- 路由注册：`backend/app/api/router.py`
- 前端调用封装：`frontend/src/api/export.ts`
- 前端交互页面：`frontend/src/pages/ReviewExportPage.tsx`

文件放置遵循项目规划文档的模块化要求：导出核心逻辑放在 `engines/export_service`，HTTP 接口放在 `api`，前端页面与 API client 分离。

## API

### POST `/api/v1/export/artifact?format=xlsx`

`format` 可选值：

- `json`
- `csv`
- `xlsx`

请求体核心结构：

```json
{
  "suite": {
    "id": "suite-001",
    "name": "Login suite",
    "test_cases": []
  },
  "requirements": [],
  "test_cases": [],
  "coverage_items": [],
  "options": {
    "include_requirements": true,
    "include_test_cases": true,
    "include_coverage": true,
    "include_summary": true,
    "file_basename": "intellitest_export"
  }
}
```

## 导出字段

测试用例导出字段对齐 ISTQB/ISO 风格：

- `test_case_id`
- `requirement_id`
- `title`
- `precondition`
- `test_steps`
- `test_data`
- `expected_result`
- `technique`
- `priority`
- `risk_score`
- `coverage_items`
- `modified_by_user`

这些字段可以体现测试用例、需求、风险与覆盖项之间的可追溯关系。

## 人工审查后的导出策略

成员 E 的前端页面会优先导出用户已经审查和修改后的数据，而不是直接从后端重新取旧数据。原因是作业要求工具必须体现设计者参与，支持对覆盖项、策略和测试用例的交互式修改。

当前流程为：

1. 成员 A/B/C/D 生成需求、风险、测试用例、预言等结果。
2. 成员 E 页面读取最近一次测试套件。
3. 用户在可编辑表格中修改测试标题、步骤、数据、预期结果、优先级和覆盖项。
4. 前端记录修改历史，并将 `modified_by_user` 标记为 `true`。
5. 导出服务将审查后的结果输出为 JSON/CSV/Excel。

## 当前数据生命周期与限制

当前 FR 6.0 导出页面处理的是“当前会话中的最近一次测试套件”，不是后端数据库中的完整历史测试结果。该设计用于支持课程演示中的即时审查和即时导出，但它不是长期持久化的测试管理模块。

具体表现如下：

- 需求原文、结构化结果和风险分析结果由后端数据库保存，因此 Docker 或后端服务重启后仍可在需求列表中看到。
- 黑盒测试用例、综合测试套件、白盒状态模型、测试预言结果和审查修改历史当前没有完整写入后端数据库。
- 审查导出页面主要读取当前浏览器会话中最近一次生成或保存的测试套件。
- 如果用户生成 A 需求的测试用例后没有导出，又继续生成 B 需求或重新生成 A 需求的测试套件，导出页面会以最新结果为准，旧的待导出结果可能被覆盖。
- 后端容器或服务重启后，后端内存中的测试套件会丢失；如果前端会话中也没有保留对应数据，审查导出页面会显示暂无待导出用例。

因此，当前功能的推荐使用方式是：每次生成一批测试结果后，先进入审查导出页面完成检查和导出，再继续生成下一批需求的测试结果。

这一限制已经整理为后续改进建议，见 `docs/improvement-proposals/test_suite_persistence_proposal.md`。

## 后续可扩展点

- 将导出记录写入数据库，形成长期审查日志。
- 持久化测试套件、测试用例、覆盖项和测试预言结果，支持跨重启恢复。
- 在审查导出页面增加历史测试套件选择功能。
- 增加 TestRail/Zephyr 字段映射模板。
- 增加按需求、风险等级、测试技术筛选后导出。
- 增加导出前的 Schema 校验报告。
