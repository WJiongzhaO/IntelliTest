# Juice Shop 测试需求资产

基于 [OWASP Juice Shop](https://github.com/juice-shop/juice-shop) 源码整理，供 IntelliTest 导入、风险分析与分模块测试设计使用。

本地源码克隆路径：`target-apps/juice-shop`（`git clone` 后分析，不纳入版本库）。

## 文件说明

| 文件 | 说明 |
|------|------|
| `juice_shop_requirements.csv` | 全应用需求库（**138 条**，**18 模块**） |
| `MODULE_INDEX.md` | 模块与 CSV **行号范围**对照 |
| `REQUIREMENTS_ANALYSIS.md` | 源码分析、两套需求说明、交付路径 |
| `CSV_GENERATION_PROMPT.md` | 生成 CSV + 索引的 LLM 提示词 |
| `OWASP_Juice_Shop_综合测试计划(1).md` | 综合测试计划 |
| `OWASP_Juice_Shop_风险分析报告.md` | FR 2.0 风险分析（10% 交付） |
| `JuiceShop登录模块详细测试设计与执行文档(1).md` | 登录模块详细设计与执行（30% 交付） |
| `risk_register.csv` | 风险登记册 |
| `generate_uniform_requirements.py` | 重新生成全量 CSV 与索引 |
| `update_module_index.py` | 更新模块索引 |

项目根 `login_requirements.csv`（LR-xxx，36 条）为**登录模块详细设计专项**；终稿用例见 `人工优化/`。用例流水线中间产物见 `未优化/`、`优化/`。

## 快速使用

```bash
curl -F "file=@fixtures/juice-shop/juice_shop_requirements.csv" http://localhost:8000/api/v1/requirements/upload
```

测试流程与执行见 [docs/详细测试设计与执行文档.md](../../docs/详细测试设计与执行文档.md)。
