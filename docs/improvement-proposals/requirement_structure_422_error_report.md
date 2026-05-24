# 需求结构化接口 422 报错分析报告

## 1. 问题概述

在前端「需求输入」页面中，用户先录入一条原始需求，随后在需求列表中点击「结构化」并确认后，前端收到如下错误：

```text
Request failed with status code 422
```

后端控制台同时出现如下关键日志：

```text
POST /api/v1/requirements/{requirement_id}/structure HTTP/1.1 422 Unprocessable Entity
Structuring failed ... AsyncClient.__init__() got an unexpected keyword argument 'proxies'
```

该错误发生在需求结构化接口处理过程中，属于 FR 1.1「需求结构化」功能链路。

## 2. 相关模块与责任归属

根据《IntelliTest 项目规划文档.md》的成员分工：

| 功能 | 模块 | 负责成员 |
| --- | --- | --- |
| FR 1.0 | 输入解析 | 成员 A |
| FR 1.1 | 需求结构化 | 成员 A |

本次报错接口为：

```text
POST /api/v1/requirements/{requirement_id}/structure
```

对应后端代码位置：

```text
backend/app/api/requirements.py
backend/app/engines/requirement_structurer/llm_client.py
```

因此，从功能归属上看，该问题应归入成员 A 的需求结构化模块。

## 3. 错误含义

HTTP 422 表示后端收到了请求，也匹配到了正确接口，但在处理请求时无法生成有效结果。

本项目中，前端点击「结构化」后会调用后端结构化接口。后端再调用 LLM SDK，将自然语言需求解析为结构化 JSON 字段，包括：

- `input_fields`
- `data_ranges`
- `conditions`
- `expected_actions`

当前错误并不是前端传参格式错误，而是后端在初始化 LLM 客户端时失败。

## 4. 根因分析

当前虚拟环境中的关键依赖版本为：

```text
openai==1.35.3
httpx==0.28.1
```

`backend/requirements.txt` 中存在如下约束：

```text
openai==1.35.3
httpx>=0.25.0
```

该组合存在兼容性风险：`openai==1.35.3` 在内部创建 HTTP 客户端时可能传入 `proxies` 参数，但 `httpx==0.28.1` 已不再接受该参数，导致报错：

```text
AsyncClient.__init__() got an unexpected keyword argument 'proxies'
```

这会使需求结构化流程在真正调用 LLM 之前失败，最终由后端接口返回 422。

## 5. 为什么前端无法通过适配解决

前端当前请求已经成功到达正确接口，接口路径和调用时机都是正确的。

从日志看，失败发生在后端内部的 LLM 客户端初始化阶段，而不是：

- 前端 URL 错误
- 前端请求方法错误
- 前端缺少 `requirement_id`
- 前端提交的数据结构错误

因此，前端无法通过修改请求参数来真正修复该问题。前端最多只能优化错误提示，例如提示「后端 LLM 依赖版本不兼容，请检查 openai/httpx 版本」。

## 6. 对测试流程的影响

该问题会阻断如下测试主流程：

```text
需求录入 -> 需求结构化 -> 风险分析 -> 黑盒/白盒测试生成 -> 测试预言 -> 审查导出
```

由于后续成员 B/C/D/E 的功能大多依赖结构化需求作为输入，因此 FR 1.1 失败会导致后续集成测试无法顺利进行。

## 7. 临时本地解决方案

为了继续本地联调，可以在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m pip install "httpx<0.28"
```

然后重启后端服务：

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

该方案属于本地依赖降级 workaround，用于恢复结构化接口运行。

## 8. 建议正式修复方案

建议由成员 A 或项目负责人统一处理后端依赖锁定，避免不同成员环境中出现不一致行为。

可选修复方向：

1. 在 `backend/requirements.txt` 中将 `httpx` 约束为兼容版本，例如：

   ```text
   httpx<0.28
   ```

2. 或升级 OpenAI Python SDK 到兼容 `httpx==0.28.x` 的版本，并执行回归测试。

3. 修复后至少验证：

   - `POST /api/v1/requirements/text`
   - `POST /api/v1/requirements/{id}/structure`
   - 结构化结果是否写回数据库
   - 前端需求列表是否显示「已结构化」

