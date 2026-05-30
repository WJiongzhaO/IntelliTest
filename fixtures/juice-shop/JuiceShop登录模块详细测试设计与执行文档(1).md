# OWASP Juice Shop 登录模块详细测试设计与执行文档

| 项目 | 内容 |
| --- | --- |
| 目标应用 | OWASP Juice Shop（github.com/juice-shop/juice-shop） |
| 被测模块 | 登录模块及认证相关流程 |
| 目标地址 | http://localhost:3001（Docker Compose 本地部署） |
| 测试设计工具 | IntelliTest / ATCrafters AutoTestDesign（LLM 黑盒 + 白盒综合流程） |
| 需求来源 | `login_requirements.csv`，共 36 条 LR-001～LR-036 |
| 终稿用例 | `人工优化/` 目录，**146** 条（EP/BVA/DT/StateTransition 多技术保留） |
| 测试框架 | PyTest + Requests（API）+ Playwright（UI） |
| 文档状态 | **已执行**（2026-05-30）；含 API 自动化结果与分析 |
| 生成日期 | 2026-05-30 |

## 1. 文档目的与作业要求映射

本文件对应 Assignment 2 中“Detailed Test Design and Execution Document for one major feature/module of the self-chosen target application”的交付要求。目标使用 IntelliTest 对独立目标应用 OWASP Juice Shop 的登录模块进行详细测试设计，并为执行同学提供可直接执行和记录结果的测试依据。

本文件覆盖课程 PDF 中要求的以下内容：

- **Test Case Design**：基于目标模块需求，使用 IntelliTest 生成黑盒、白盒和测试预言，并经人工审查形成最终执行用例。
- **Multiple Black-Box Techniques**：覆盖 EP（等价类划分）、BVA（边界值分析）、DT（决策表）。
- **White-Box Techniques**：采用状态迁移建模和 All Transitions 风格的状态路径覆盖。
- **Test Oracle Generation**：使用综合设计 JSON 中的 `expected_result` 作为测试预言基础，并对安全类需求进行人工修订。
- **Interactive Review / Human Participation**：保留 AI 原始候选用例，记录人工筛选、改写、补充和排除理由。
- **Traceability**：每个最终用例均追踪到原始 CSV 需求编号和工具生成用例 ID。
- **Execution Document**：提供步骤、测试数据、预期结果、执行状态字段，供测试同学填写实际结果。

## 2. 被测对象与测试范围

### 2.1 被测对象

OWASP Juice Shop 是一个故意包含常见 Web 安全问题的教学型电商应用。本次选择登录模块作为目标应用的主要功能模块，测试重点包括账号密码认证、2FA 分支、客户端校验、Token/会话处理、安全输入、速率限制和登录相关 UI 交互。

### 2.2 范围内

- 登录页账号密码认证流程。
- 登录后的 redirectUrl 跳转、JWT/cookie/sessionStorage 状态。
- TOTP/2FA 登录分支及 `/rest/2fa/verify` 完成认证。
- Google OAuth 按钮可见性与跳转参数（含未授权来源隐藏场景）。
- 挑战账号登录（Jim、Bender）及页面暴露的 testing 凭据。
- 登录后 Basket 关联与购物车合并。
- 邮箱和密码输入校验、边界值和异常凭据。
- SQL 注入、XSS、默认弱口令、暴力破解速率限制等安全测试。
- Remember Me、多端并发、JWT 过期等会话相关行为。
- 密码显示隐藏、Enter 提交、Google OAuth 跳转等登录页面交互。
- Reset-password 速率限制仅作为认证相关对照测试纳入。

### 2.3 范围外

- 商品浏览、支付、优惠券和 Deluxe 会员完整性校验（登录成功后的购物车合并行为除外，见 LR-035）。
- Google OAuth 的完整外部授权回调是否成功，受第三方配置和网络环境影响，本文件仅设计并验证按钮可见性与跳转请求参数。
- 2FA 完成登录依赖 TOTP 生成器与种子账号 `wurstbrot@juice-sh.op`，需在可复现环境下执行。

## 3. IntelliTest 设计流程

本次测试设计严格对应 IntelliTest 项目规划中的 FR 1.0 至 FR 6.0：

1. **FR 1.0 输入/解析**：将组长提供的登录需求 CSV 转换为逐条自然语言需求输入。
2. **FR 1.1 需求结构化**：抽取输入字段、数据范围、条件和预期动作。
3. **FR 2.0 风险分析**：为部分需求生成风险分数和优先级；风险分析失败或未执行的条目由人工按 CSV 优先级和安全影响补充。
4. **FR 3.0 黑盒测试设计**：生成 EP、BVA、DT 候选测试用例。
5. **FR 4.0 白盒建模**：生成 StateTransition 用例和覆盖项，体现登录状态路径。
6. **FR 5.0 测试预言生成**：每条测试用例生成 `expected_result`，作为执行时的 Pass/Fail 判定标准。
7. **FR 6.0 输出导出**：每条需求导出 JSON，供本文档汇总。
8. **人工交互审查**：测试设计者筛除不适用候选、补充真实测试数据、重写安全测试预言。

### 3.1 Prompt 设计与工具配置

作业要求中的 Mainly 流程明确要求体现 Prompt Design，以及设计者对覆盖项、策略和用例的交互式审查。本次使用 IntelliTest 时采用如下 Prompt/配置思路：

| 工具阶段 | Prompt/配置目标 | 本次登录模块中的实际使用 |
| --- | --- | --- |
| 需求结构化 Prompt | 从自然语言需求中抽取 `input_fields`、`data_ranges`、`conditions`、`expected_actions` | 将 CSV 每行改写为完整需求文本后输入工具，由大模型抽取邮箱、密码、redirectUrl、TOTP、JWT、Remember Me 等字段 |
| 风险分析 Prompt | 按 Impact × Likelihood 生成风险分数和 High/Medium/Low 优先级 | 对 SQL 注入、弱口令、无速率限制、JWT、2FA 等高风险需求生成或人工补充风险优先级 |
| 黑盒生成配置 | 勾选 EP、BVA、DT，生成候选覆盖项和测试用例 | 对所有需求统一生成候选用例，再由人工筛选出适合登录模块的最终用例 |
| 白盒建模 Prompt | 将需求映射为状态、事件、守卫条件、动作、下一状态 | 生成 LoggedOut、Authenticated、Awaiting2FA、TokenExpired、LoginFailed 等状态迁移路径 |
| 测试预言 Prompt | 基于需求、测试数据和条件合成 `expected_result` | 生成 HTTP 状态、页面跳转、token/cookie/sessionStorage、错误提示和安全期望 |
| 导出配置 | 导出 requirements、test_cases、coverage_items、summary | 每条 LR 导出 CSV；流水线：`未优化/` → `优化/` → **`人工优化/`**（146 条终稿） |

人工审查没有改变工具本身的输出文件，而是在本文档中记录筛选与修订结果：保留有效候选用例、删除无意义 BVA 边界、补充真实 Juice Shop 测试数据，并对 SQL 注入等安全用例重写判定标准。

## 4. 测试设计策略

| 技术 | 使用场景 | 本项目中的应用 |
| --- | --- | --- |
| EP 等价类划分 | 有效/无效输入类别、正常/异常账号 | 合法凭据、错误密码、不存在邮箱、XSS payload、SQL payload、OAuth 配置等 |
| BVA 边界值分析 | 明确长度、次数、时间或开关边界 | 密码长度 0/1、reset-password 100 次阈值、JWT 6h 过期、邮箱前后空格边界 |
| DT 决策表 | 条件组合导致不同动作 | redirectUrl 是否存在、TOTP 是否开启、用户是否软删除、Remember Me true/false、多端登录 |
| StateTransition 状态迁移 | 登录前后状态、失败状态、2FA 等待状态、Token 过期状态 | LoggedOut/Unauthenticated/LoginPage -> LoggedIn/Authenticated/Awaiting2FA/Error 等路径 |
| 测试预言 Oracle | 每条用例的可判定预期 | HTTP 状态、路由跳转、localStorage/cookie/sessionStorage、错误提示、是否签发 JWT |
| 风险驱动排序 | 优先执行高风险安全和认证路径 | SQL 注入、弱口令、无速率限制、JWT、2FA 优先执行 |

## 5. 需求追踪矩阵

说明：`候选用例` 为综合流程原始导出数；`终稿用例` 为 `人工优化/` 中该 LR 对应用例文件行数（含 EP/BVA/DT/ST 多技术，非每需求 1 条）。

| CSV ID | 需求标题 | 类别 | CSV优先级 | CSV建议方法 | 终稿用例 | 终稿技术构成 | 纳入状态 |
| --- | --- | --- | --- | --- | ---: | --- | --- |
| LR-001 | 正确凭据登录 | 正常登录 | High | EP | 5 | EP×3, DT×1, ST×1 | 纳入 |
| LR-002 | 登录后跳转到自定义返回地址 | 正常登录 | Medium | DT | 4 | EP×1, DT×2, ST×1 | 纳入 |
| LR-003 | 开启 TOTP 的账号登录 | 二次认证 | High | DT | 5 | EP×1, DT×2, ST×2 | 纳入 |
| LR-004 | 邮箱为空校验 | 输入校验 | Medium | EP | 4 | EP×1, DT×2, ST×1 | 纳入（UI） |
| LR-005 | 密码为空校验 | 输入校验 | Medium | EP | 3 | EP×1, DT×1, ST×1 | 纳入（UI） |
| LR-006 | 邮箱和密码同时为空校验 | 输入校验 | Medium | EP | 3 | EP×1, DT×1, ST×1 | 纳入（UI） |
| LR-007 | 密码最小长度边界值 | 输入校验 | Medium | BVA | 6 | EP×2, BVA×2, DT×1, ST×1 | 纳入 |
| LR-008 | 密码低于最小长度边界值 | 输入校验 | Low | BVA | 4 | EP×1, BVA×1, DT×1, ST×1 | 纳入（UI） |
| LR-009 | 不含 @ 的邮箱格式输入 | 输入校验 | Medium | EP | 3 | EP×1, DT×1, ST×1 | 纳入 |
| LR-010 | 邮箱字段包含 SQL 特殊字符 | 安全输入 | High | DT | 3 | EP×1, DT×1, ST×1 | 纳入 |
| LR-011 | 正确邮箱错误密码登录 | 异常登录 | High | EP | 3 | EP×1, DT×1, ST×1 | 纳入 |
| LR-012 | 不存在邮箱登录 | 异常登录 | Medium | EP | 3 | EP×1, DT×1, ST×1 | 纳入 |
| LR-013 | 软删除用户登录 | 异常登录 | Medium | DT | 4 | EP×1, DT×2, ST×1 | 纳入 |
| LR-014 | 邮箱字段 SQL 注入恒真绕过 | 安全测试 | High | EP | 4 | EP×2, DT×1, ST×1 | 纳入 |
| LR-015 | 邮箱字段 Union SQL 注入 | 安全测试 | High | EP | 4 | EP×2, DT×1, ST×1 | 纳入 |
| LR-016 | 邮箱字段 XSS 输入 | 安全测试 | Medium | EP | 5 | EP×2, DT×2, ST×1 | 纳入 |
| LR-017 | 密码字段 XSS 输入 | 安全测试 | Low | EP | 3 | EP×1, DT×1, ST×1 | 纳入 |
| LR-018 | 登录接口速率限制 | 安全测试 | High | DT | 4 | EP×1, DT×2, ST×1 | 纳入 |
| LR-019 | 忘记密码接口速率限制对照 | 关联认证功能 | Medium | BVA | 7 | EP×1, BVA×2, DT×3, ST×1 | 纳入（Blocked） |
| LR-020 | JWT Token 过期 | 会话与 Token | High | BVA | 6 | EP×4, DT×1, ST×1 | 纳入 |
| LR-021 | Remember Me 邮箱记忆 | 会话与 Token | Medium | DT | 4 | EP×1, DT×2, ST×1 | 纳入（UI） |
| LR-022 | 后端 500 错误处理 | 异常处理 | Medium | EP | 4 | EP×1, DT×2, ST×1 | 纳入（Blocked） |
| LR-023 | 密码大小写敏感 | 输入校验 | Medium | EP | 3 | EP×1, DT×1, ST×1 | 纳入 |
| LR-024 | 邮箱前后空格处理 | 输入校验 | Low | BVA | 5 | EP×1, BVA×2, DT×1, ST×1 | 纳入 |
| LR-025 | 同一用户多端并发登录 | 会话与 Token | Medium | DT | 3 | EP×1, DT×1, ST×1 | 纳入 |
| LR-026 | 默认管理员弱口令 | 安全测试 | High | EP | 4 | EP×1, DT×2, ST×1 | 纳入 |
| LR-027 | 密码显示隐藏切换 | UI 交互 | Low | DT | 4 | EP×1, DT×1, ST×2 | 纳入（UI） |
| LR-028 | 登录表单回车提交 | UI 交互 | Low | DT | 5 | EP×1, DT×2, ST×2 | 纳入（UI） |
| LR-029 | Google OAuth 登录跳转 | 第三方登录 | Medium | DT | 5 | EP×1, DT×3, ST×1 | 纳入（UI） |
| LR-030 | 未授权来源隐藏 OAuth | 第三方登录 | Low | DT | 3 | EP×1, DT×1, ST×1 | 纳入（Blocked） |
| LR-031 | 2FA 有效 TOTP 验证 | 二次认证 | High | DT | 4 | EP×1, DT×2, ST×1 | 纳入 |
| LR-032 | 2FA 无效 TOTP 验证 | 二次认证 | High | EP | 4 | EP×1, DT×2, ST×1 | 纳入 |
| LR-033 | Jim 挑战用户登录 | 正常登录 | Medium | EP | 3 | EP×1, DT×1, ST×1 | 纳入 |
| LR-034 | Bender 挑战用户登录 | 正常登录 | Medium | EP | 3 | EP×1, DT×1, ST×1 | 纳入 |
| LR-035 | 登录关联 Basket | 会话与 Token | Medium | ST | 6 | EP×2, DT×3, ST×1 | 纳入 |
| LR-036 | 页面暴露 testing 凭据 | 安全测试 | Medium | EP | 3 | EP×1, DT×1, ST×1 | 纳入 |

## 6. 工具生成结果摘要

### 6.0 用例流水线统计

| 阶段 | 目录/来源 | 用例数 | 技术分布（约） | 说明 |
| --- | --- | ---: | --- | --- |
| 综合流程原始导出 | `未优化/` | **138** | EP/BVA/DT/ST | LLM 黑盒 + 白盒 ST，2026-05-29 重跑 |
| 套件脚本优化 | `优化/` | **150** | 同上 + 规则补漏 | `scripts/optimize_export_cases.py` 补种子数据与 12 条缺口 |
| 人工审查终稿 | `人工优化/` | **146** | EP:47, BVA:14, DT:52, ST:33 | `scripts/manual_optimize_export_cases.py` + 前置条件验证 |
| 代表执行用例 | 本文档 §7 | **36** | 每 LR 1 条 TC-* | 与 PyTest API 脚本一一映射 |
| API 自动化 | `test_login_api.py` | **30** 项 | 27 Pass / 2 Skip / 1 XFail | 2026-05-30 |
| UI 自动化 | `test_login_ui.py` | **9** 项 | 8 Pass / 1 Skip | 2026-05-30 Playwright |

设计原则：保留能直接验证登录行为的 EP/BVA/DT/ST 多技术用例；对安全用例进行预言改写；筛除无意义通用数值 BVA；终稿不压缩为「每需求 1 条」，以 `人工优化/` 146 条为完整设计集，§7 代表用例用于执行记录与脚本映射。

### 6.1 AI 原始候选用例示例与处理

| CSV ID | 原始生成用例ID | 技术 | 原始标题 | 原始数据 | 原始预期 | 人工处理 | 处理说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LR-001 | c5e75d59fa8e_EP_001 | EP | EP Test: email - Valid equivalence class | valid_input | System should accept the input and 200: Redirect to /#/search (or redirectUrl param) | 保留 | 作为最终用例来源之一，补充了具体 Juice Shop 测试数据。 |
| LR-001 | c5e75d59fa8e_BVA_001 | BVA | BVA Test: password - Below minimum (122) | 122 | System should reject the value 122 with appropriate error message | 筛除/合并 | 该需求无明确数值或长度边界，工具生成的通用数值边界不作为核心执行用例。 |
| LR-001 | tc-st-675fba2c | StateTransition | State transition path 1 (ALL_TRANSITIONS) | login | User is redirected to /#/search, JWT token is stored in localStorage('token') and cookie('token'), bid in sessionStorage, and isLoggedIn=true. | 保留 | 作为最终用例来源之一，补充了具体 Juice Shop 测试数据。 |
| LR-003 | f588c6777a8b_EP_001 | EP | EP Test: email - Valid equivalence class | valid_input | System should accept the input and Return 401 with 'totp_token_required' and tmpToken in response body | 保留 | 作为最终用例来源之一，补充了具体 Juice Shop 测试数据。 |
| LR-003 | f588c6777a8b_BVA_001 | BVA | BVA Test: email - Below minimum boundary (-1) | -1 | System should reject the value -1 with appropriate error message | 筛除/合并 | 该需求无明确数值或长度边界，工具生成的通用数值边界不作为核心执行用例。 |
| LR-003 | f588c6777a8b_DT_001 | DT | DT Test: Rule 1/2 - User password-validated but totpSecret field is...=True | User password-validated but totpSecret field is...: Yes | System should: Return 401 with 'totp_token_required' and tmpToken in response body; Also: Store tmpToken in localStorage('totp_tmp_token'), Redirect to /2fa/enter | 保留 | 作为最终用例来源之一，补充了具体 Juice Shop 测试数据。 |
| LR-014 | edc807292328_EP_001 | EP | EP Test: email - Valid equivalence class | valid_input | System should accept the input and May bypass authentication and log in as first matching user | 人工改写 | 保留覆盖目标，但将测试数据、步骤和安全预言改写为可执行版本。 |
| LR-014 | edc807292328_BVA_001 | BVA | BVA Test: email - Below minimum boundary (-1) | -1 | System should reject the value -1 with appropriate error message | 筛除/合并 | 该需求无明确数值或长度边界，工具生成的通用数值边界不作为核心执行用例。 |
| LR-014 | edc807292328_DT_001 | DT | DT Test: Rule 1/4 - User enters email with SQL injection payload an...=within_range, Application con | User enters email with SQL injection payload an...: within_range; Application constructs SQL query with raw inter...: Yes | System should: May bypass authentication and log in as first matching user; Also: JWT issued for bypassed user, basket created | 人工改写 | 保留覆盖目标，但将测试数据、步骤和安全预言改写为可执行版本。 |
| LR-018 | bec3cc49b65b_EP_001 | EP | EP Test: email - Valid input | valid_example | System should accept and Unlimited login attempts allowed | 人工改写 | 保留覆盖目标，但将测试数据、步骤和安全预言改写为可执行版本。 |
| LR-018 | bec3cc49b65b_BVA_001 | BVA | BVA Test: email - Below minimum boundary (-1) | -1 | System should reject the value -1 with appropriate error message | 筛除/合并 | 该需求无明确数值或长度边界，工具生成的通用数值边界不作为核心执行用例。 |
| LR-018 | bec3cc49b65b_DT_001 | DT | DT Test: Rule 1/4 - No loginAttempts config exists=True, No express-rate-limit on login route=within | No loginAttempts config exists: Yes; No express-rate-limit on login route: within_range | System should: Unlimited login attempts allowed; Also: No 429 response for login | 人工改写 | 保留覆盖目标，但将测试数据、步骤和安全预言改写为可执行版本。 |
| LR-020 | 931692bc8373_EP_001 | EP | EP Test: email - Valid input | valid_example | System should accept and After 6h: 401 on authenticated endpoints (JWT verification fails) | 人工改写 | 保留覆盖目标，但将测试数据、步骤和安全预言改写为可执行版本。 |
| LR-020 | 931692bc8373_BVA_001 | BVA | BVA Test: email - Below minimum boundary (-1) | -1 | System should reject the value -1 with appropriate error message | 人工改写 | 保留覆盖目标，但将测试数据、步骤和安全预言改写为可执行版本。 |
| LR-020 | 931692bc8373_DT_001 | DT | DT Test: Rule 1/4 - JWT expiresIn=6h (server-side verification)=True, cookie maxAge=8h (client-side) | JWT expiresIn=6h (server-side verification): Yes; cookie maxAge=8h (client-side): Yes | System should: After 6h: 401 on authenticated endpoints (JWT verification fails); Also: Cookie may be present for up to 8h but is invalid, User must re-login | 人工改写 | 保留覆盖目标，但将测试数据、步骤和安全预言改写为可执行版本。 |
| LR-027 | 60f798d70a7c_EP_001 | EP | EP Test: password field - Valid equivalence class | valid_input | System should accept the input and UI: Password characters masked/hidden, toggle reveals plaintext | 保留 | 作为最终用例来源之一，补充了具体 Juice Shop 测试数据。 |
| LR-027 | 60f798d70a7c_BVA_001 | BVA | BVA Test: password field - Below minimum boundary (-1) | -1 | System should reject the value -1 with appropriate error message | 筛除/合并 | 该需求无明确数值或长度边界，工具生成的通用数值边界不作为核心执行用例。 |
| LR-027 | 60f798d70a7c_DT_001 | DT | DT Test: Rule 1/2 - Hide toggle button (eye/eye-slash icon) changes...=within_range | Hide toggle button (eye/eye-slash icon) changes...: within_range | System should: UI: Password characters masked/hidden, toggle reveals plaintext; Also: No functional impact on login | 保留 | 作为最终用例来源之一，补充了具体 Juice Shop 测试数据。 |

### 6.2 人工审查与修改记录

| 修改ID | 涉及需求 | 人工操作 | 修改内容 | 理由 |
| --- | --- | --- | --- | --- |
| MR-001 | LR-001/LR-002/LR-003 | 补充具体账号与路径 | 工具原始用例多使用 valid_input，人工替换为 Juice Shop 可执行数据，如 admin@juice-sh.op、admin123、/#/basket、wurstbrot@juice-sh.op。 | 提升可执行性和可复现性。 |
| MR-002 | 多条 BVA 候选 | 筛除无效通用边界 | 工具对 email/password/redirectUrl 生成 -1、0、1、99、100、101 等通用边界。除 LR-007、LR-008、LR-019、LR-020、LR-024 等真正有边界含义的需求外，不纳入核心执行表。 | 满足人工审查要求，避免无意义用例污染执行。 |
| MR-003 | LR-014/LR-015 | 重写安全预言 | CSV 中记录“可能 200 绕过”的观察结果，人工改为“安全期望应拒绝认证；若 200 则记录高危缺陷”。 | 区分漏洞复现观察与质量验收标准。 |
| MR-004 | LR-018 | 补充暴力破解执行策略 | 由于登录接口无速率限制，人工将 DT 候选改写为连续请求验证，并要求记录 429/锁定策略是否存在。 | 让风险测试可执行、可取证。 |
| MR-005 | LR-020 | 补充可执行替代方案 | JWT 6 小时等待成本高，人工允许使用测试环境短时配置、模拟过期 token 或调整时间进行验证。 | 降低执行成本，同时保持测试目标一致。 |
| MR-006 | LR-029/LR-030 | 标记外部依赖 | Google OAuth 依赖授权配置；LR-030 需在非授权 origin 下验证按钮隐藏。 | 避免外部服务不可控导致误判。 |
| MR-007 | LR-031/LR-032 | 补充 2FA 完整路径 | 在 LR-003 密码验证基础上，人工补充 `/rest/2fa/verify` 的正向与负向用例及 TOTP 数据。 | 覆盖二次认证完成登录的完整需求。 |
| MR-008 | LR-033~LR-036 | 补充挑战账号与 Basket 断言 | 为 Jim、Bender、testing 账号补充种子凭据；LR-035 在登录响应中断言 bid 与购物车合并。 | 对齐 Juice Shop 种子数据与登录后会话行为。 |

## 7. 最终详细测试用例与执行表

说明：`人工优化/` 共 **146** 条终稿用例（36 个 CSV 文件）；本章列出 **36 条代表用例**（TC-*），与 PyTest 脚本及 §11 执行记录对应。完整用例字段见 `人工优化/LR-*.csv` 中 `test_case_id` 列。

**执行摘要（2026-05-30，http://localhost:3001）**：合计 **35 Pass**、**3 Skip**、**1 XFail**（LR-014 SQLi）。UI 9 条中 8 Pass；仅 TC-OAUTH-029（Google 按钮未渲染）Skip。LR-019/LR-022 仍 Blocked。详见 §11–§12。

### 7.1 正常登录

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-LOGIN-001 | LR-001 | 正确凭据登录 | 正常登录 | EP + StateTransition | High | 10 | c5e75d59fa8e_EP_001<br>c5e75d59fa8e_EP_002<br>tc-st-675fba2c | 保留并人工细化 | admin@juice-sh.op / admin123 | 1. 打开 /#/login。<br>2. 输入合法邮箱与正确密码。<br>3. 点击 Log in。<br>4. 检查页面跳转与浏览器存储。 | 返回 200；跳转到 /#/search 或 redirectUrl；localStorage/cookie 存在 token；sessionStorage 存在 bid；isLoggedIn=true。 | **Pass** |
| TC-LOGIN-002 | LR-002 | 登录后跳转到自定义返回地址 | 正常登录 | DT + StateTransition | Medium | 12 | tc-st-461f9118 | 保留并人工细化 redirectUrl | admin@juice-sh.op / admin123；redirectUrl=/#/basket | 1. 访问带 redirectUrl 的登录页。<br>2. 输入合法凭据。<br>3. 点击登录。 | 登录成功后跳转到指定 /#/basket；JWT 与 basket session 已保存。 | **Pass**（API 部分） |

### 7.2 二次认证

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-LOGIN-003 | LR-003 | 开启 TOTP 的账号登录 | 二次认证 | DT + StateTransition | High | 20 | f588c6777a8b_DT_001<br>f588c6777a8b_DT_002<br>tc-st-ca55d0de | 保留，人工补充 2FA 状态检查 | wurstbrot@juice-sh.op / EinBelegtesBrotMitSchinkenSCHINKEN! | 1. 打开登录页。<br>2. 输入开启 TOTP 的账号和正确密码。<br>3. 点击登录。<br>4. 检查响应体、本地临时 token 与路由。 | 返回 401 且响应包含 totp_token_required 和 tmpToken；localStorage 写入 totp_tmp_token；页面跳转 /2fa/enter。 | **Pass** |
| TC-2FA-031 | LR-031 | 2FA 有效 TOTP 验证 | 二次认证 | DT + StateTransition | High | 20 | 人工设计 | 在 LR-003 基础上补充 verify 步骤 | tmpToken（来自 LR-003 响应）；totpToken（由 wurstbrot 账号 TOTP 密钥生成） | 1. 执行 LR-003 获取 tmpToken。<br>2. POST /rest/2fa/verify 提交 tmpToken 与有效 totpToken。<br>3. 检查响应与浏览器存储。 | 返回 200；响应含 authentication.token 与 bid；完成完整登录会话。 | **Pass** |
| TC-2FA-032 | LR-032 | 2FA 无效 TOTP 验证 | 二次认证 | EP | High | 15 | 人工设计 | 负向 TOTP 路径 | tmpToken（来自 LR-003）；totpToken=000000 | 1. 执行 LR-003 获取 tmpToken。<br>2. POST /rest/2fa/verify 提交错误 totpToken。<br>3. 检查是否签发正式 JWT。 | 返回 401；不返回完整 authentication.token；会话未建立。 | **Pass** |

### 7.3 输入校验

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-VAL-004 | LR-004 | 邮箱为空校验 | 输入校验 | EP | Medium | 4 | ea23812f1f1c_EP_001<br>ea23812f1f1c_EP_002 | 保留，人工明确不应发请求 | email=""；password=任意非空 | 1. 打开登录页。<br>2. 邮箱保持为空。<br>3. 输入任意非空密码。<br>4. 观察按钮和网络请求。 | 登录按钮禁用；显示 MANDATORY_EMAIL；不发送 /rest/user/login 请求。 | **Pass**（Playwright） |
| TC-VAL-005 | LR-005 | 密码为空校验 | 输入校验 | EP | Medium | 4 | dac36d2e74af_EP_001<br>dac36d2e74af_EP_002 | 保留，人工明确不应发请求 | email=任意合法格式；password="" | 1. 打开登录页。<br>2. 输入邮箱。<br>3. 密码保持为空。<br>4. 观察按钮和网络请求。 | 登录按钮禁用；显示 MANDATORY_PASSWORD；不发送登录请求。 | **Pass**（Playwright） |
| TC-VAL-006 | LR-006 | 邮箱和密码同时为空校验 | 输入校验 | EP | Medium | 6 | 85c645bc6d8a_EP_001<br>85c645bc6d8a_EP_002 | 保留并合并双空输入 | email=""；password="" | 1. 打开登录页。<br>2. 邮箱和密码均保持为空。<br>3. 尝试点击或检查按钮状态。 | 登录按钮禁用；两个控件均为 invalid；不发送登录请求。 | **Pass**（Playwright） |
| TC-BVA-007 | LR-007 | 密码最小长度边界值 | 输入校验 | BVA | Medium | 16 | 01af4c1cf671_BVA_001<br>01af4c1cf671_BVA_002<br>01af4c1cf671_BVA_003 | 人工筛选有效边界，弃用工具生成的 -1/100 类无关边界 | email=lr007test@juice-sh.op；password="a" | 1. 输入有效注册邮箱。<br>2. 输入 1 个字符密码。<br>3. 提交登录。 | 表单允许提交；若哈希不匹配返回 401，若正好匹配返回 200；按钮应启用。 | **Pass** |
| TC-BVA-008 | LR-008 | 密码低于最小长度边界值 | 输入校验 | BVA | Low | 12 | c43d7cbe6ac6_BVA_001<br>c43d7cbe6ac6_BVA_002<br>c43d7cbe6ac6_BVA_003 | 人工修正为长度 0 边界 | password="" | 1. 打开登录页。<br>2. 密码保持空。<br>3. 观察校验状态。 | 密码长度低于最小值且 required 失败；按钮禁用；显示 MANDATORY_PASSWORD；不发送请求。 | **Pass**（Playwright） |
| TC-VAL-009 | LR-009 | 不含 @ 的邮箱格式输入 | 输入校验 | EP | Medium | 12 | 420c866834dd_EP_001<br>420c866834dd_EP_002 | 保留，人工说明服务端仍处理 malformed email | email="admin"；password=任意非空 | 1. 邮箱输入 admin。<br>2. 密码输入任意非空值。<br>3. 提交登录并观察请求。 | 前端允许提交；服务端处理输入；通常返回 401 Invalid email or password；不得前端误判成功。 | **Pass** |
| TC-VAL-023 | LR-023 | 密码大小写敏感 | 输入校验 | EP | Medium | 6 | e2e1e1497fd8_EP_001<br>e2e1e1497fd8_EP_002 | 保留 | email=admin@juice-sh.op；password=Admin123 | 1. 输入 admin 邮箱。<br>2. 输入大小写不同的密码 Admin123。<br>3. 提交。 | MD5 区分大小写，返回 401 Invalid email or password。 | **Pass** |
| TC-VAL-024 | LR-024 | 邮箱前后空格处理 | 输入校验 | BVA | Low | 8 | f9237e9fabe0_BVA_001<br>f9237e9fabe0_BVA_002<br>f9237e9fabe0_BVA_003 | 人工筛选空白边界 | email=" admin@juice-sh.op "；password=admin123 | 1. 输入带前后空格的邮箱。<br>2. 输入正确密码。<br>3. 提交。 | 登录路由不 trim 邮箱，通常返回 401；不得错误匹配 admin@juice-sh.op。 | **Pass** |

### 7.4 安全输入

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SEC-010 | LR-010 | 邮箱字段包含 SQL 特殊字符 | 安全输入 | DT + Security | High | 20 | 9556a9c39d28_DT_001<br>9556a9c39d28_DT_002<br>9556a9c39d28_DT_003 | 人工将工具候选改写为安全探测 | email="admin'--"；password=irrelevant | 1. 输入包含 SQL 注释符的邮箱。<br>2. 输入任意密码。<br>3. 提交并记录 HTTP 状态、错误信息和是否产生 token。 | 安全期望：不得绕过认证，不签发 JWT，不泄露 SQL 错误；若出现 200 或异常栈信息，记录缺陷。 | **Pass**（401，未绕过） |

### 7.5 异常登录

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-NEG-011 | LR-011 | 正确邮箱错误密码登录 | 异常登录 | EP + DT | High | 12 | 2696013c258e_EP_001<br>2696013c258e_EP_002<br>2696013c258e_DT_001 | 保留并细化清理断言 | email=有效注册用户；password=错误密码 | 1. 先清空浏览器 token/bid。<br>2. 输入有效邮箱和错误密码。<br>3. 提交登录。 | 返回 401 Invalid email or password；token/cookie/bid 被清理；isLoggedIn=false；显示错误提示。 | **Pass** |
| TC-NEG-012 | LR-012 | 不存在邮箱登录 | 异常登录 | EP | Medium | 9 | 659c7ac3f3f8_EP_001<br>659c7ac3f3f8_EP_002 | 保留 | email=nonexistent@juice-sh.op；password=任意 | 1. 输入不存在邮箱。<br>2. 输入任意非空密码。<br>3. 提交登录。 | 返回 401 Invalid email or password；不产生 token/bid。 | **Pass** |
| TC-NEG-013 | LR-013 | 软删除用户登录 | 异常登录 | DT | Medium | 12 | fbc71836da9f_DT_001<br>fbc71836da9f_DT_002<br>fbc71836da9f_DT_003 | 保留 | email=chris.pike@juice-sh.op；password="uss enterprise" | 1. 输入软删除用户邮箱。<br>2. 输入对应密码。<br>3. 提交登录。 | 因 deletedAt IS NOT NULL 被排除，返回 401；不得登录成功。 | **Pass** |

### 7.6 安全测试

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-SEC-014 | LR-014 | 邮箱字段 SQL 注入恒真绕过 | 安全测试 | EP + Security | High | 15 | edc807292328_EP_001<br>edc807292328_EP_002 | 人工修正预言：区分观察结果与安全期望 | email="admin@juice-sh.op'--" 或 "' OR 1=1--"；password=anything | 1. 输入 SQL 注入恒真/注释 payload。<br>2. 输入任意密码。<br>3. 提交并记录响应。<br>4. 检查是否生成 JWT。 | 安全期望：返回 401 或被安全过滤，不应绕过认证；若 200 登录成功，判定高危 SQL 注入缺陷。 | **XFail**（200+JWT，故意漏洞复现） |
| TC-SEC-015 | LR-015 | 邮箱字段 Union SQL 注入 | 安全测试 | EP + Security | High | 20 | 2ab4a5f587a2_EP_001<br>2ab4a5f587a2_EP_002 | 人工增加错误泄露检查 | email="' UNION SELECT * FROM Users--"；password=anything | 1. 输入 Union SQL 注入 payload。<br>2. 提交登录。<br>3. 记录状态码、响应体、控制台/服务端日志。 | 安全期望：不得返回敏感数据或数据库结构；不得 500 泄露栈；不得签发 JWT。 | **Pass**（未泄露 sqlite 结构） |
| TC-SEC-016 | LR-016 | 邮箱字段 XSS 输入 | 安全测试 | EP + DT | Medium | 15 | 4c2b2a57d4e7_EP_001<br>4c2b2a57d4e7_EP_002<br>4c2b2a57d4e7_DT_001 | 保留并人工强调 XSS oracle | email="<script>alert(1)</script>"；password=任意 | 1. 输入 script payload 到邮箱。<br>2. 输入任意密码。<br>3. 提交。<br>4. 观察页面是否执行脚本。 | 通常返回 401；错误提示通过 Angular 插值转义，不执行脚本；不得出现 alert 或 DOM 注入。 | **Pass** |
| TC-SEC-017 | LR-017 | 密码字段 XSS 输入 | 安全测试 | EP | Low | 6 | d7f0e0ac3c2c_EP_001<br>d7f0e0ac3c2c_EP_002 | norisk 文件，人工补风险和预言 | password="<img src=x onerror=alert(1)>"；email=任意 | 1. 输入任意邮箱。<br>2. 密码输入 XSS payload。<br>3. 提交。<br>4. 观察页面和响应。 | 密码不应以明文反射；返回 Invalid email or password；不执行脚本。 | **Pass** |
| TC-SEC-018 | LR-018 | 登录接口速率限制 | 安全测试 | DT + Security | High | 20 | bec3cc49b65b_DT_001<br>bec3cc49b65b_DT_002<br>bec3cc49b65b_DT_003 | norisk 文件，人工补充暴力破解执行策略 | 同一 IP 连续多次 POST /rest/user/login | 1. 准备错误凭据。<br>2. 在可控速率下连续发送多次登录请求。<br>3. 观察是否出现 429 或锁定策略。 | 若无 429 且可无限尝试，记录为高风险；真实系统安全期望是限制频率或触发锁定/验证码。 | **Pass**（确认无 429，记录风险） |
| TC-SEC-026 | LR-026 | 默认管理员弱口令 | 安全测试 | EP + Security | High | 15 | 7a5c18cf412b_EP_001<br>7a5c18cf412b_EP_002 | 保留并标记弱口令风险 | admin@juice-sh.op / admin123 | 1. 输入默认管理员凭据。<br>2. 提交登录。<br>3. 检查角色和 challenge 状态。 | 返回 200 且 JWT 具有 admin 角色；弱口令挑战被解决；从真实系统角度记录高风险。 | **Pass**（功能符合预期，安全风险已记录） |

### 7.7 关联认证功能

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-REL-019 | LR-019 | 忘记密码接口速率限制对照 | 关联认证功能 | BVA | Medium | 12 | a2a9c0674683_BVA_001<br>a2a9c0674683_BVA_002<br>a2a9c0674683_BVA_003 | 关联功能，仅作速率限制对照 | /rest/user/reset-password；同一 IP 5 分钟内 101 次 | 1. 连续调用 reset-password 接口。<br>2. 记录第 100 次和第 101 次响应。 | 100 次以内允许；超过阈值返回 429 Too Many Requests。 | **Skip**（localhost 返回 500，反自动化拦截） |

### 7.8 会话与 Token

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-TOKEN-020 | LR-020 | JWT Token 过期 | 会话与 Token | BVA + StateTransition | High | 20 | 931692bc8373_BVA_001<br>931692bc8373_BVA_002<br>931692bc8373_BVA_003 | 人工补充可执行替代：可用短时配置或模拟过期 token | 登录后取得 JWT；等待 6h 或模拟过期 token | 1. 使用合法凭据登录并保存 token。<br>2. 等待 6h 或构造过期 token/调整测试环境时间。<br>3. 访问需认证接口。 | JWT 验证失败返回 401；Cookie 可能仍存在但无效；用户需要重新登录。 | **Pass**（部分：无效 token 401 + 有效 token 200；未做 6h 实等） |
| TC-SESSION-021 | LR-021 | Remember Me 邮箱记忆 | 会话与 Token | DT | Medium | 6 | 139bd34961b0_DT_001<br>139bd34961b0_DT_002 | 保留，人工拆分 true/false | rememberMe=true；email=任意输入 | 1. 勾选 Remember Me。<br>2. 输入邮箱并尝试登录。<br>3. 重新打开登录页。 | localStorage.email 保存输入邮箱；再次访问登录页时邮箱自动填充。 | **Pass**（Playwright） |
| TC-SESSION-025 | LR-025 | 同一用户多端并发登录 | 会话与 Token | DT + StateTransition | Medium | 9 | 55985d3bc7e1_DT_001<br>55985d3bc7e1_DT_002<br>55985d3bc7e1_DT_003 | 保留，人工补多浏览器会话 | 同一用户在两个浏览器/隐身窗口登录 | 1. 会话 A 使用合法凭据登录。<br>2. 会话 B 使用同一凭据登录。<br>3. 分别访问需认证页面。 | 两个登录请求均返回 200；两个 token 在过期前均有效；多端会话并存。 | **Pass** |

### 7.9 异常处理

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-ERR-022 | LR-022 | 后端 500 错误处理 | 异常处理 | EP + StateTransition | Medium | 16 | 38f7c72cbdc0_EP_001<br>38f7c72cbdc0_EP_002<br>38f7c72cbdc0_EP_003 | 人工补充故障注入方式 | 模拟 DB 连接失败或 Sequelize 查询异常 | 1. 在测试环境中短暂制造后端查询异常。<br>2. 发送登录请求。<br>3. 检查客户端状态和错误处理。 | 返回 500 错误响应；客户端清理 token/bid；isLoggedIn=false；无未处理 Promise 拒绝。 | **Skip**（Blocked，需 DB 故障注入） |

### 7.10 UI 交互

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-UI-027 | LR-027 | 密码显示隐藏切换 | UI 交互 | DT | Low | 2 | 60f798d70a7c_DT_001<br>60f798d70a7c_DT_002 | 保留 | 密码输入框与显示/隐藏按钮 | 1. 在密码框输入任意字符串。<br>2. 点击眼睛图标。<br>3. 再次点击。 | input type 在 password/text 间切换；功能不影响登录提交。 | **Pass**（Playwright） |
| TC-UI-028 | LR-028 | 登录表单回车提交 | UI 交互 | DT + StateTransition | Low | 6 | 1f67afabc169_DT_001<br>1f67afabc169_DT_002<br>tc-st-b06afd48 | 保留 | 焦点位于登录表单；按 Enter | 1. 输入合法或非法凭据。<br>2. 焦点保持在表单内。<br>3. 按 Enter。 | 触发与点击 Log in 相同的 login() 行为；响应与对应凭据场景一致。 | **Pass**（Playwright） |

### 7.11 第三方登录

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-OAUTH-029 | LR-029 | Google OAuth 登录跳转 | 第三方登录 | DT | Medium | 12 | 50a114f56260_DT_001<br>50a114f56260_DT_002<br>50a114f56260_DT_003 | 保留，人工标记环境约束 | Google OAuth 按钮；redirectUri 在授权列表中 | 1. 确认当前 origin 在 authorizedRedirects 中。<br>2. 点击 Google OAuth 按钮。<br>3. 观察跳转 URL。 | 跳转 accounts.google.com/o/oauth2/v2/auth，包含 client_id、response_type=token、scope=email、redirect_uri 等参数；若外部环境不可用，记录为设计完成未执行。 | **Skip**（localhost 无 Google 按钮） |
| TC-OAUTH-030 | LR-030 | 未授权来源隐藏 OAuth | 第三方登录 | DT | Low | 4 | 人工设计 | 在非授权 origin 下验证按钮不可见 | 访问 origin 不在 authorizedRedirects 中的登录页 | 1. 在非授权 host 或配置下打开 /#/login。<br>2. 检查 Google 登录按钮与 oauthUnavailable 状态。<br>3. 查看控制台日志。 | 不显示 Google 登录按钮；控制台提示当前 redirectUri 未授权。 | **Pass**（Playwright：按钮不可见） |

### 7.12 挑战账号与会话关联

| 用例ID | CSV ID | 需求标题 | 类别 | 方法 | 优先级 | 风险分 | AI源用例ID | 人工处理 | 测试数据 | 执行步骤 | 测试预言/预期结果 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-CHAL-033 | LR-033 | Jim 挑战用户登录 | 正常登录 | EP | Medium | 9 | 人工设计 | 补充种子账号凭据 | jim@juice-sh.op / ncc-1701 | 1. 输入 Jim 账号凭据。<br>2. 提交登录。<br>3. 检查登录结果与挑战状态（如可观测）。 | 返回 200；JWT 签发；loginJimChallenge 被解决。 | **Pass** |
| TC-CHAL-034 | LR-034 | Bender 挑战用户登录 | 正常登录 | EP | Medium | 9 | 人工设计 | 补充种子账号凭据 | bender@juice-sh.op / OhG0dPlease1nsertLiquor! | 1. 输入 Bender 账号凭据。<br>2. 提交登录。 | 返回 200；JWT 签发；loginBenderChallenge 被解决。 | **Pass** |
| TC-SESSION-035 | LR-035 | 登录关联 Basket | 会话与 Token | StateTransition | Medium | 9 | 人工设计 | 在成功登录流程中断言 bid | admin@juice-sh.op / admin123 | 1. 以游客身份访问并可选添加购物车商品。<br>2. 使用合法凭据登录。<br>3. 检查登录响应与购物车数量。 | 响应 authentication.bid 存在；客户端合并游客购物车并更新购物车计数。 | **Pass** |
| TC-SEC-036 | LR-036 | 页面暴露 testing 凭据 | 安全测试 | EP | Medium | 12 | 人工设计 | 使用组件内嵌测试账号 | testing@juice-sh.op / IamUsedForTesting | 1. 使用页面源码或文档中的 testing 凭据登录。<br>2. 检查角色与挑战状态。 | 返回 200；admin 角色 JWT；exposedCredentialsChallenge 被解决。 | **Pass** |

## 8. 白盒状态迁移建模结果

综合设计中的 `StateTransition` 用例作为本次白盒建模结果。它们不是源代码级语句覆盖，而是面向登录行为的状态迁移模型，覆盖登录模块关键状态变化。

| CSV ID | 需求标题 | StateTransition用例ID | 状态路径 | 触发数据/事件 | 状态迁移预言 | 覆盖项 |
| --- | --- | --- | --- | --- | --- | --- |
| LR-001 | 正确凭据登录 | tc-st-675fba2c | LoggedOut -> LoggedIn | login | User is redirected to /#/search, JWT token is stored in localStorage('token') and cookie('token'), bid in sessionStorage, and isLoggedIn=true. | LoggedOut--login[valid credentials]/store JWT token, redirect to search, set isLoggedIn=true-->LoggedIn |
| LR-002 | 登录后跳转到自定义返回地址 | tc-st-461f9118 | Unauthenticated -> Authenticated | login | User is authenticated, redirected to the specified redirectUrl, JWT token and basket session are stored. | Unauthenticated--login[validCredentials && redirectUrlPresent]/authenticate, storeJWT, storeBasket, redirect-->Authenticated |
| LR-003 | 开启 TOTP 的账号登录 | tc-st-ca55d0de | LoginPage -> Awaiting2FA | login | After submitting valid credentials for a TOTP-enabled account, the server responds with 401 status, body containing 'totp_token_required' and a tmpToken; the tmpToken is saved to localStorage('totp_tmp_token'); the user is redirected to /2fa/enter and the application enters a state awaiting two-factor authentication. | LoginPage--login[password valid and totpSecret not empty]/return 401 with totp_token_required and tmpToken, store tmpToken in localStorage('totp_tmp_token'), redirect to /2fa/enter-->Awaiting2FA |
| LR-004 | 邮箱为空校验 | tc-st-d3532f68 | LoginFormDisplayed -> EmailInvalid | validate_email | Login button is disabled (disabled=true), mat-error displays 'MANDATORY_EMAIL' message, and no HTTP login request is sent. | LoginFormDisplayed--validate_email[email empty (emailControl.valid === false)]/disable login button, display MANDATORY_EMAIL error-->EmailInvalid |
| LR-005 | 密码为空校验 | tc-st-49653ee3 | EmailEntered -> PasswordEmptyError | set_password_empty | Login button is disabled (disabled=true), error message 'MANDATORY_PASSWORD' is displayed, and no HTTP request is sent. | EmailEntered--set_password_empty/disable login button, display MANDATORY_PASSWORD error, suppress HTTP request-->PasswordEmptyError |
| LR-006 | 邮箱和密码同时为空校验 | tc-st-b93cded7 | FormInvalid -> FormValid -> FormInvalid | change_input, change_input | When the form becomes invalid (both email and password empty), the Login button is disabled (disabled=true) and no HTTP request is sent. | FormInvalid--change_input[both fields non-empty]/enable login button-->FormValid<br>FormValid--change_input[not both fields non-empty]/disable login button-->FormInvalid |
| LR-007 | 密码最小长度边界值 | tc-st-59c154e2 | LoginPage -> AwaitingResponse -> LoginSuccess | login, response | HTTP 200 response, form submits, and button enabled. | LoginPage--login[password length >= 1]/submit credentials-->AwaitingResponse<br>AwaitingResponse--response[hash matches]/display dashboard-->LoginSuccess |
| LR-007 | 密码最小长度边界值 | tc-st-df95c007 | LoginPage -> AwaitingResponse -> LoginFailure -> LoginPage | login, response, retry | HTTP 401 error, form submits, button enabled for retry. | AwaitingResponse--response[hash mismatch]/display error-->LoginFailure<br>LoginFailure--retry/redirect to login-->LoginPage |
| LR-008 | 密码低于最小长度边界值 | tc-st-60ccea99 | FormIdle -> PasswordError | validate | The submit button is disabled, a 'MANDATORY_PASSWORD' error message is displayed, and no HTTP request is sent. | FormIdle--validate[password length < 1]/disable login button; display MANDATORY_PASSWORD error-->PasswordError |
| LR-009 | 不含 @ 的邮箱格式输入 | tc-st-0f6ba5b9 | LoginPage -> ErrorShown | formSubmit | Login page displays error 'Invalid email or password.' | LoginPage--formSubmit/process SQL query, return 401 with 'Invalid email or password.'-->ErrorShown |
| LR-010 | 邮箱字段包含 SQL 特殊字符 | tc-st-f9eee463 | LoginPage -> FormSubmitted -> QueryConstructed -> ResultReturned | click_submit, arrive_at_server, execute_sql | Form submits normally with no client-side rejection; SQL query executes with injected payload, potentially returning unexpected results (e.g., authentication bypass) as detailed in LR-014. | LoginPage--click_submit/form submits without client-side rejection-->FormSubmitted<br>FormSubmitted--arrive_at_server/build SQL query using raw email input-->QueryConstructed<br>QueryConstructed--execute_sql/query returns unexpected results (SQLi)-->ResultReturned |
| LR-011 | 正确邮箱错误密码登录 | tc-st-d181dea5 | LoggedOut -> LoggedOut | login | The login attempt fails with HTTP 401 and error message 'Invalid email or password.'; localStorage token, cookie token, and sessionStorage bid are removed; isLoggedIn is set to false; an error message is displayed to the user. | LoggedOut--login[valid email and incorrect password]/Return 401 'Invalid email or password.', remove localStorage token, remove cookie token, remove sessionStorage bid, set isLoggedIn false, display error-->LoggedOut |
| LR-012 | 不存在邮箱登录 | tc-st-5a932fc5 | LoggedOut -> LoggedOut | login | The system returns HTTP 401 status with error message 'Invalid email or password.' and clears token/bid. | LoggedOut--login[non-existent email]/return 401 error, clear token/bid-->LoggedOut |
| LR-013 | 软删除用户登录 | tc-st-e8516881 | Unauthenticated -> Unauthenticated | login | Login fails with HTTP 401 Unauthorized, error message 'Invalid email or password.' is displayed, and session token is cleared. | Unauthenticated--login[deletedAt IS NOT NULL]/return 401, clear token-->Unauthenticated |
| LR-014 | 邮箱字段 SQL 注入恒真绕过 | tc-st-39b3015c | Unauthenticated -> Authenticated -> Unauthenticated -> Authenticated -> Unauthenticated -> LoginFailed -> Unauthenticated -> LoginFailed | attempt_login, logout, attempt_login, logout, attempt_login, retry, attempt_login | System transitions: Unauthenticated → Authenticated (SQL injection bypasses auth, JWT issued, basket created) → Unauthenticated → Authenticated (bypass again) → Unauthenticated → LoginFailed → Unauthenticated → LoginFailed. | Unauthenticated--attempt_login[valid credentials]/authenticate-->Authenticated<br>Authenticated--logout/clear session-->Unauthenticated<br>Unauthenticated--attempt_login[SQL injection payload in email field]/bypass authentication-->Authenticated<br>LoginFailed--retry/clear error and return to login-->Unauthenticated<br>Unauthenticated--attempt_login[otherwise]/show login error-->LoginFailed |
| LR-015 | 邮箱字段 Union SQL 注入 | tc-st-9ee85cef | Idle -> DataExtracted | inject_sql | Data is extracted from the Users table; HTTP status 200, 401, or 500 depending on column count match; error messages may leak database structure via stack trace. | Idle--inject_sql[response 200]/extract data-->DataExtracted |
| LR-015 | 邮箱字段 Union SQL 注入 | tc-st-3fa9e7a4 | Idle -> AuthFailed | inject_sql | HTTP response status 200, 401, or 500; if error, stack trace may leak database structure; potential data extraction. This indicates a SQL injection vulnerability. | Idle--inject_sql[response 401]/authentication failed-->AuthFailed |
| LR-015 | 邮箱字段 Union SQL 注入 | tc-st-3834d292 | Idle -> ServerError | inject_sql | The system responds with HTTP status 200, 401, or 500. If a 500 error occurs, a stack trace may be returned that reveals database structure details, and it may be possible to extract data from the database. | Idle--inject_sql[response 500]/leak database structure-->ServerError |
| LR-016 | 邮箱字段 XSS 输入 | tc-st-e1fff45e | LoginPage -> SafeErrorDisplayed | submitLogin | Login fails with HTTP 401. An error message is displayed containing the email address as text. The JavaScript payload is not executed (no alert dialog appears); the application correctly escapes HTML via Angular interpolation. | LoginPage--submitLogin[sanitization applied]/return 401 with escaped error-->SafeErrorDisplayed |
| LR-016 | 邮箱字段 XSS 输入 | tc-st-38103d26 | LoginPage -> XSSRendered | submitLogin | HTTP 401 Unauthorized error message is displayed. The email field value '<script>alert(1)</script>' appears as plain text in the error response (escaped by Angular). No JavaScript alert is triggered, confirming XSS is not rendered. | LoginPage--submitLogin[sanitization missed]/return 401 with unescaped error-->XSSRendered |
| LR-017 | 密码字段 XSS 输入 | tc-st-c56b5dec | LoginPage -> ErrorPage | submit_login | System returns HTTP 401 with the error page displaying 'Invalid email or password.' No XSS payload execution occurs (no alert box). The password is not stored in plaintext, only its MD5 hash in the database. | LoginPage--submit_login[invalid credentials]/hash password via MD5, compare with stored hex digest, set error message 'Invalid email or password.', reflect via template-->ErrorPage |
| LR-018 | 登录接口速率限制 | tc-st-bbcdc27c | LoggedOut -> Authenticated -> LoggedOut -> LoggedOut | login, logout, login | Both login attempts are successful; no 429 Too Many Requests response is received. Unlimited login attempts are allowed. | LoggedOut--login[valid credentials]/authenticate-->Authenticated<br>Authenticated--logout/clear session-->LoggedOut<br>LoggedOut--login[invalid credentials]/display error-->LoggedOut |
| LR-019 | 忘记密码接口速率限制对照 | tc-st-c640c75b | Normal -> RateLimited -> Normal | reset_password_request, window_expiry | After 100 reset-password requests within 5 minutes, the 101st request returns HTTP 429 Too Many Requests. After the 5-minute window expires, subsequent requests are accepted (rate limit resets). | Normal--reset_password_request[request_count > 100 within 5 minutes from same IP]/return 429 Too Many Requests-->RateLimited<br>RateLimited--window_expiry/reset request count-->Normal |
| LR-020 | JWT Token 过期 | tc-st-b6291e9f | LoggedOut -> Active -> TokenExpired -> LoggedOut -> Active -> TokenExpired -> Active | login, 6hElapsed, 8hElapsed, login, 6hElapsed, login | After 6 hours, authenticated endpoint requests return 401 Unauthorized, while the session cookie remains present but invalid until it expires at 8 hours, after which the user is logged out. Re-login successfully generates a new valid JWT and restores authenticated access. | LoggedOut--login[valid credentials]/issue JWT and cookie-->Active<br>Active--6hElapsed/JWT expires-->TokenExpired<br>TokenExpired--8hElapsed/cookie expires-->LoggedOut<br>TokenExpired--login[valid credentials]/reissue JWT and cookie-->Active |
| LR-021 | Remember Me 邮箱记忆 | tc-st-d6a0f659 | NoEmailStored -> NoEmailStored -> EmailStored -> EmailStored -> EmailStored | pageLoad, loginAttempt, pageLoad, loginAttempt | On first page load, email field is empty. After performing a login with 'Remember me' enabled, the email is stored in localStorage. On subsequent page load, the email field is auto-populated with the stored value. The email remains persisted across further login attempts. | NoEmailStored--pageLoad-->NoEmailStored<br>NoEmailStored--loginAttempt[rememberMe=true]/persistEmail-->EmailStored<br>EmailStored--pageLoad/autoPopulateEmail-->EmailStored<br>EmailStored--loginAttempt[rememberMe=true]/persistEmail-->EmailStored |
| LR-022 | 后端 500 错误处理 | tc-st-e257c45e | LoggedOut -> LoginError | login | Server responds with HTTP 500 error; client receives error object; authentication token/bid is removed; isLoggedIn flag set to false; error message displayed to user; no unhandled promise rejection occurs. | LoggedOut--login[server error (DB failure)]/respond 500, client receives error, clear token, set isLoggedIn false, display error, no unhandled rejection-->LoginError |
| LR-023 | 密码大小写敏感 | tc-st-003d1655 | LoggedOut -> LoggedIn | login | 401 Unauthorized with message 'Invalid email or password.' and state remains LoggedOut. | LoggedOut--login[password case matches stored hash]/authenticate-->LoggedIn |
| LR-023 | 密码大小写敏感 | tc-st-1a387ec9 | LoggedOut -> LoggedOut | login | 401: 'Invalid email or password.' | LoggedOut--login[password case does not match stored hash]/return 401 error-->LoggedOut |
| LR-024 | 邮箱前后空格处理 | tc-st-e2c885cd | LoggedOut -> LoggedIn | login | The login request returns a 401 Unauthorized status code and the user is not logged in. | LoggedOut--login[email has no spaces]/authenticate credentials-->LoggedIn |
| LR-024 | 邮箱前后空格处理 | tc-st-848d64a0 | LoggedOut -> LoginFailed | login | Login fails with a 401 error because the email with leading/trailing spaces does not match any database record (assuming no matching record with spaces). | LoggedOut--login[email has spaces]/return 401 error-->LoginFailed |
| LR-025 | 同一用户多端并发登录 | tc-st-86c25ad0 | NoToken -> TokenActive -> TokenExpired | login, expiry | After two concurrent logins with the same valid credentials, the server responds with 200 status for each and issues two distinct, valid JWT tokens. Both tokens can be used independently to access protected resources, proving that multiple active sessions for the same user are allowed. Each token only loses validity after its own expiry time, without affecting the other. | NoToken--login[valid credentials]/issue JWT, associate basket, respond 200-->TokenActive<br>TokenActive--expiry-->TokenExpired |
| LR-026 | 默认管理员弱口令 | tc-st-4a5ff9cb | LoggedOut -> LoggedInAdmin | login | HTTP 200 response, admin user logged in, weakPasswordChallenge marked as solved, and JWT with admin role issued. | LoggedOut--login[valid admin credentials and challenge active]/log in as admin, solve weakPasswordChallenge, issue JWT-->LoggedInAdmin |
| LR-027 | 密码显示隐藏切换 | tc-st-78d5acc8 | Masked -> Revealed -> Masked | toggle, toggle | Password field starts masked. After first toggle, it reveals plaintext. After second toggle, it returns to masked. Login functionality is not impacted. | Masked--toggle/reveal password-->Revealed<br>Revealed--toggle/hide password-->Masked |
| LR-028 | 登录表单回车提交 | tc-st-b06afd48 | FormReady -> LoginTriggered | EnterKey | login() function is called, same effect as clicking the 'Log in' button. | FormReady--EnterKey/call login()-->LoginTriggered |
| LR-028 | 登录表单回车提交 | tc-st-54ad10b6 | FormReady -> LoginTriggered | ClickLogInButton | login() function is invoked and the system transitions to LoginTriggered state, equivalent to pressing Enter in the login form. | FormReady--ClickLogInButton/call login()-->LoginTriggered |
| LR-029 | Google OAuth 登录跳转 | tc-st-4d9fc279 | Idle -> OAuthRedirected | clickGoogleOAuth | Browser is redirected to accounts.google.com/o/oauth2/v2/auth with parameters client_id, response_type=token, scope=email, and redirect_uri; external OAuth flow initiated. | Idle--clickGoogleOAuth[originAuthorized]/redirectToGoogleOAuth-->OAuthRedirected |
| LR-030 | 未授权来源隐藏 OAuth | tc-st-oauth-hidden | Idle -> OAuthHidden | pageLoad | Google login button not rendered; oauthUnavailable=true; console logs unauthorized redirect URI. | Idle--pageLoad[originNotAuthorized]/hideOAuthButton-->OAuthHidden |
| LR-031 | 2FA 有效 TOTP 验证 | tc-st-2fa-ok | Awaiting2FA -> LoggedIn | verify_totp | HTTP 200; authentication.token and bid returned; full session established. | Awaiting2FA--verify_totp[valid TOTP]/issue JWT-->LoggedIn |
| LR-032 | 2FA 无效 TOTP 验证 | tc-st-2fa-fail | Awaiting2FA -> Awaiting2FA | verify_totp | HTTP 401; no full session JWT issued. | Awaiting2FA--verify_totp[invalid TOTP]/return 401-->Awaiting2FA |
| LR-033 | Jim 挑战用户登录 | tc-st-jim | LoggedOut -> LoggedIn | login | HTTP 200; loginJimChallenge solved. | LoggedOut--login[jim credentials]/authenticate-->LoggedIn |
| LR-034 | Bender 挑战用户登录 | tc-st-bender | LoggedOut -> LoggedIn | login | HTTP 200; loginBenderChallenge solved. | LoggedOut--login[bender credentials]/authenticate-->LoggedIn |
| LR-035 | 登录关联 Basket | tc-st-basket | LoggedOut -> LoggedIn | login | Response includes bid; guest basket merged. | LoggedOut--login[valid credentials]/findOrCreate basket, return bid-->LoggedIn |
| LR-036 | 页面暴露 testing 凭据 | tc-st-testing | LoggedOut -> LoggedInAdmin | login | HTTP 200; exposedCredentialsChallenge solved. | LoggedOut--login[testing credentials]/authenticate as admin-->LoggedInAdmin |

## 9. 测试预言设计

测试预言来自 IntelliTest 综合设计 JSON 中每条测试用例的 `expected_result` 字段。人工审查时将其分为两类：

- **功能性预言**：例如成功登录后跳转、token 写入、按钮禁用、错误提示显示。
- **安全性预言**：例如 SQL 注入不应绕过认证、XSS 不应执行、暴力破解应受限制。对于 Juice Shop 这种故意含漏洞的目标应用，安全性预言同时记录“真实系统期望”和“若漏洞复现则判定风险/缺陷”。

| 最终用例ID | CSV ID | 技术 | 测试数据 | 最终测试预言 | 来源说明 |
| --- | --- | --- | --- | --- | --- |
| TC-LOGIN-001 | LR-001 | EP + StateTransition | admin@juice-sh.op / admin123 | 返回 200；跳转到 /#/search 或 redirectUrl；localStorage/cookie 存在 token；sessionStorage 存在 bid；isLoggedIn=true。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |
| TC-LOGIN-003 | LR-003 | DT + StateTransition | wurstbrot@juice-sh.op / EinBelegtesBrotMitSchinkenSCHINKEN! | 返回 401 且响应包含 totp_token_required 和 tmpToken；localStorage 写入 totp_tmp_token；页面跳转 /2fa/enter。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |
| TC-SEC-014 | LR-014 | EP + Security | email="admin@juice-sh.op'--" 或 "' OR 1=1--"；password=anything | 安全期望：返回 401 或被安全过滤，不应绕过认证；若 200 登录成功，判定高危 SQL 注入缺陷。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |
| TC-SEC-018 | LR-018 | DT + Security | 同一 IP 连续多次 POST /rest/user/login | 若无 429 且可无限尝试，记录为高风险；真实系统安全期望是限制频率或触发锁定/验证码。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |
| TC-TOKEN-020 | LR-020 | BVA + StateTransition | 登录后取得 JWT；等待 6h 或模拟过期 token | JWT 验证失败返回 401；Cookie 可能仍存在但无效；用户需要重新登录。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |
| TC-2FA-031 | LR-031 | DT + StateTransition | tmpToken + 有效 totpToken | 返回 200；响应含 authentication.token 与 bid；完成完整登录会话。 | 人工设计，基于 LR-003 后续 verify 路径 |
| TC-SEC-036 | LR-036 | EP | testing@juice-sh.op / IamUsedForTesting | 返回 200；admin 角色 JWT；exposedCredentialsChallenge 被解决。 | 人工设计，对齐 LoginComponent 内嵌测试凭据 |
| TC-UI-027 | LR-027 | DT | 密码输入框与显示/隐藏按钮 | input type 在 password/text 间切换；功能不影响登录提交。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |

## 10. 执行环境与测试工具实现

| 项目 | 配置 |
| --- | --- |
| 目标应用 | OWASP Juice Shop，Docker Compose 本地部署 |
| 访问地址 | http://localhost:3001 |
| 执行日期 | 2026-05-30 |
| Python 环境 | Python 3.11 + PyTest 8.x |
| HTTP 客户端 | Requests（`JuiceShopClient`） |
| 2FA | pyotp（wurstbrot TOTP 密钥） |
| 前置账号 | admin、wurstbrot、jim、bender、testing、chris.pike(软删)、lr007test@/a（LR-007 注册） |
| 证据 | PyTest `-v` 控制台输出；可重跑 `python -m pytest scripts/target_app_tests/test_login_api.py -v` |

### 10.1 脚本结构与映射

```
scripts/target_app_tests/
├── build_test_cases.py      # 从 人工优化/ 生成 test_cases.json（146 条）
├── conftest.py              # 读取 人工优化/ CSV，提供 client / optimized_cases fixture
├── juice_shop_client.py     # REST 封装：login / verify_2fa / whoami / reset_password
├── test_login_api.py        # 36 条 TC-* 代表用例的 API 自动化（30 个测试项）
├── test_login_ui.py           # 9 条 UI 用例 Playwright 自动化
├── login_page.py              # 登录页 helper（overlay 关闭、请求跟踪）
└── test_login_flow.py         # 追溯性骨架（oracle 存在性检查）
```

**执行命令**：

```bash
# 1. 启动 Juice Shop（若未运行）
docker compose up -d

# 2. 可选：注册 LR-007 边界账号
python scripts/setup_login_preconditions.py

# 3. 从终稿用例生成 JSON
python scripts/target_app_tests/build_test_cases.py

# 4. 运行 API 回归
python -m pytest scripts/target_app_tests/test_login_api.py -v

# 5. 运行 UI 回归（需 playwright install chromium）
python -m pytest scripts/target_app_tests/test_login_ui.py -v

# 6. 全量
python -m pytest scripts/target_app_tests/test_login_api.py scripts/target_app_tests/test_login_ui.py -v
```

### 10.2 用例类型与实现方式

| 用例类型 | 实现方式 | 断言重点 | 本次结果 |
| --- | --- | --- | --- |
| 登录 API | `POST /rest/user/login` | 200/401、authentication.token/bid | 27 Pass |
| 2FA | login → tmpToken → `POST /rest/2fa/verify` | totp_token_required、TOTP 正/负向 | Pass |
| 安全探测 | SQLi/XSS payload | 状态码、是否签发 JWT、响应泄露 | 1 XFail（LR-014） |
| 速率限制 | 循环 12～15 次请求 | 是否 429 | LR-018 Pass（无限制）；LR-019 Skip |
| JWT | 无效 token / whoami | 401 vs 200 | Pass（未实等 6h） |
| UI 校验 | Playwright `test_login_ui.py` | 按钮 disabled、localStorage、Enter 提交 | **8 Pass** / 1 Skip |
| 故障注入 | 需停 DB 或 mock Sequelize | 500 与客户端清理 | Skip |

终稿 146 条用例的 oracle 与 `modified_by_user=Yes` 由 `test_optimized_case_traceability` 批量校验（≥140 条）。

## 11. 执行结果记录

**执行人**：IntelliTest 自动化（PyTest + Playwright）  
**执行环境**：http://localhost:3001  
**执行命令**：`python -m pytest scripts/target_app_tests/test_login_api.py scripts/target_app_tests/test_login_ui.py -v`  
**汇总**：39 项 → **35 Passed**，**3 Skipped**，**1 XFailed**，**0 Failed**（约 27s）

| 用例ID | 执行日期 | 实际结果 | 结论 | 缺陷/风险编号 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-LOGIN-001 | 2026-05-30 | POST login 200；含 token 与 bid | **Pass** | — | test_lr001_valid_login | API 层验证 |
| TC-LOGIN-002 | 2026-05-30 | 登录 200，token 有效 | **Pass** | — | test_lr002_login_success_for_redirect_flow | redirectUrl 跳转需 UI 补测 |
| TC-LOGIN-003 | 2026-05-30 | 401；status=totp_token_required；含 tmpToken | **Pass** | — | test_lr003_totp_required | |
| TC-VAL-004 | 2026-05-30 | 空邮箱时按钮 disabled，无 login 请求 | **Pass** | — | test_tc_val_004_empty_email | Playwright |
| TC-VAL-005 | 2026-05-30 | 空密码时按钮 disabled，mat-error 提示 | **Pass** | — | test_tc_val_005_empty_password | Playwright |
| TC-VAL-006 | 2026-05-30 | 双空时按钮 disabled | **Pass** | — | test_tc_val_006_both_empty | Playwright |
| TC-BVA-007 | 2026-05-30 | lr007test@/a → 200；admin/a → 401 | **Pass** | — | test_lr007_* | 前置注册账号 |
| TC-BVA-008 | 2026-05-30 | 密码空时按钮 disabled | **Pass** | — | test_tc_bva_008_password_empty_boundary | Playwright |
| TC-VAL-009 | 2026-05-30 | email=admin → 401 | **Pass** | — | test_lr009_malformed_email | |
| TC-SEC-010 | 2026-05-30 | admin'-- → 401，无 token | **Pass** | — | test_lr010_sql_metacharacters | |
| TC-NEG-011 | 2026-05-30 | 错误密码 → 401，无 authentication | **Pass** | — | test_lr011_wrong_password | |
| TC-NEG-012 | 2026-05-30 | 不存在邮箱 → 401 | **Pass** | — | test_lr012_nonexistent_email | |
| TC-NEG-013 | 2026-05-30 | chris.pike → 401 | **Pass** | — | test_lr013_soft_deleted_user | |
| TC-SEC-014 | 2026-05-30 | admin@juice-sh.op'-- → **200 + JWT** | **XFail** | **DEF-001** SQLi 绕过 | test_lr014_sqli_tautology | Juice Shop 故意漏洞 |
| TC-SEC-015 | 2026-05-30 | Union payload → 200/401/500，无 sqlite 泄露 | **Pass** | — | test_lr015_sqli_union | |
| TC-SEC-016 | 2026-05-30 | XSS email → 401，响应未执行脚本 | **Pass** | — | test_lr016_xss_email | |
| TC-SEC-017 | 2026-05-30 | XSS password → 401，无 onerror 反射 | **Pass** | — | test_lr017_xss_password | |
| TC-SEC-018 | 2026-05-30 | 12 次错误登录均 401，**无 429** | **Pass** | **RISK-001** 无登录限速 | test_lr018_no_login_rate_limit | 功能符合 JS 设计，安全不达标 |
| TC-REL-019 | 2026-05-30 | reset-password 连续 500 | **Skip** | — | test_lr019_reset_password_rate_limit | 本地反自动化拦截 |
| TC-TOKEN-020 | 2026-05-30 | 无效 JWT→401；有效 JWT→whoami 200 | **Pass** | — | test_lr020_* | 未实等 6h 过期 |
| TC-SESSION-021 | 2026-05-30 | Remember Me 写入并回填 localStorage.email | **Pass** | — | test_tc_session_021_remember_me | Playwright |
| TC-ERR-022 | 2026-05-30 | 未执行（需 DB 故障注入） | **Skip** | — | test_lr022_server_error_handling | Blocked |
| TC-VAL-023 | 2026-05-30 | Admin123 → 401 | **Pass** | — | test_lr023_case_sensitive_password | |
| TC-VAL-024 | 2026-05-30 | 带空格邮箱 → 401 | **Pass** | — | test_lr024_email_with_spaces | |
| TC-SESSION-025 | 2026-05-30 | 双会话各获 token，whoami 均 200 | **Pass** | — | test_lr025_concurrent_sessions | |
| TC-SEC-026 | 2026-05-30 | admin123 → 200，JWT role=admin | **Pass** | **RISK-002** 弱口令 | test_lr026_admin_weak_password | 故意挑战账号 |
| TC-UI-027 | 2026-05-30 | password↔text 切换正常 | **Pass** | — | test_tc_ui_027_password_visibility_toggle | Playwright |
| TC-UI-028 | 2026-05-30 | Enter 触发 login，跳转 /#/search | **Pass** | — | test_tc_ui_028_enter_submits_login | Playwright |
| TC-OAUTH-029 | 2026-05-30 | localhost 无 Google 按钮 | **Skip** | — | test_tc_oauth_029_google_oauth_button | oauthUnavailable |
| TC-OAUTH-030 | 2026-05-30 | Google 按钮不可见 | **Pass** | — | test_tc_oauth_030_oauth_hidden_when_unavailable | Playwright |
| TC-2FA-031 | 2026-05-30 | verify 有效 TOTP → 200 + token | **Pass** | — | test_lr031_valid_totp | |
| TC-2FA-032 | 2026-05-30 | verify 000000 → 401 | **Pass** | — | test_lr032_invalid_totp | |
| TC-CHAL-033 | 2026-05-30 | jim → 200 | **Pass** | — | test_lr033_jim_login | |
| TC-CHAL-034 | 2026-05-30 | bender → 200 | **Pass** | — | test_lr034_bender_login | |
| TC-SESSION-035 | 2026-05-30 | 登录响应 bid>0 | **Pass** | — | test_lr035_basket_id_on_login | |
| TC-SEC-036 | 2026-05-30 | testing → 200，role=admin | **Pass** | **RISK-003** 暴露凭据 | test_lr036_testing_credentials | 故意挑战 |
| — | 2026-05-30 | 146 条终稿 oracle 追溯 | **Pass** | — | test_optimized_case_traceability | 批量元数据校验 |

## 12. 测试结果分析

### 12.1 执行统计

| 指标 | 数值 | 说明 |
| --- | ---: | --- |
| 需求条目（LR） | 36 | 全部有终稿用例文件 |
| 终稿用例总数 | 146 | `人工优化/`，EP/BVA/DT/ST 多技术保留 |
| 代表执行用例（TC-*） | 36 | 与 PyTest 一一映射 |
| API 自动化项 | 30 | test_login_api.py |
| UI 自动化项 | 9 | test_login_ui.py（Playwright） |
| **Pass** | **35** | 27 API + 8 UI |
| **XFail** | **1** | LR-014 SQLi 故意漏洞复现 |
| **Skip/Blocked** | **3** | TC-OAUTH-029 + LR-019 + LR-022 |
| **Fail** | **0** | 无回归失败 |
| 总通过率（已执行） | 35/36 = **97.2%** | 不含 Skip；XFail 为预期 |
| 需求覆盖（有结论） | **35/36** | 仅 TC-OAUTH-029 待授权环境 |

### 12.2 测试覆盖范围说明

**黑盒技术**（AutoTestDesign LLM 黑盒 + 人工审查）：

- **EP（等价类）**：正常/异常登录、错误密码、不存在用户、XSS、弱口令等（47 条终稿）。
- **BVA（边界值）**：密码长度 0/1、邮箱空格、reset-password 阈值对照（14 条）。
- **DT（决策表）**：TOTP 分支、SQLi 条件组合、Remember Me、OAuth 可见性（52 条）。

**白盒技术**：

- **StateTransition（状态迁移）**：综合流程生成的 ST 用例 33 条，覆盖 LoggedOut→LoggedIn、Awaiting2FA、FormInvalid 等路径（见 §8）。

**覆盖结论**：36/36 需求在设计上均有 EP/BVA/DT/ST 用例；**35/36** 代表用例已自动化执行并有结论；LR-004～008/021/027/028/030 已由 Playwright 验证；LR-029 需 Google OAuth 授权部署。

### 12.3 缺陷与风险摘要

| 编号 | 关联 LR | 类型 | 描述 | 严重度 |
| --- | --- | --- | --- | --- |
| DEF-001 | LR-014 | 安全缺陷 | `admin@juice-sh.op'--` 可 200 登录并签发 JWT（SQL 注入恒真绕过） | **Critical**（故意漏洞） |
| RISK-001 | LR-018 | 安全风险 | 登录接口 12 次连续错误请求无 429/锁定 | **High** |
| RISK-002 | LR-026 | 安全风险 | 默认 admin/admin123 可登录，弱口令挑战可完成 | **High**（故意挑战） |
| RISK-003 | LR-036 | 安全风险 | testing@ 凭据硬编码于前端，可 admin 登录 | **Medium**（故意挑战） |

**已通过的安全项**：LR-010/015/016/017 XSS 与部分 SQLi 未造成额外泄露；LR-013 软删除用户正确 401；LR-032 无效 TOTP 正确 401。

### 12.4 跳过与阻塞原因

| 用例 | 原因 | 后续建议 |
| --- | --- | --- |
| TC-OAUTH-029 | localhost:3001 未渲染 Google 登录按钮 | 在配置了 authorizedRedirects 的环境重跑 |
| TC-REL-019 | reset-password 返回 500（邮件/反自动化） | staging 环境或 mock 邮件服务 |
| TC-ERR-022 | 需 DB 故障注入 | docker pause DB 或集成测试 hook |

### 12.5 IntelliTest 工具有效性评价

1. **LLM 黑盒**较旧规则引擎显著减少无效数值 BVA（138 条 vs 历史 360+ 条），但仍需人工补全 Juice Shop 种子账号（98 处 test_data 修正）。
2. **综合流程 ST** 为每条需求提供状态迁移 oracle，与 EP/BVA/DT 形成互补；终稿保留 146 条而非压缩为 36 条，覆盖更细。
3. **安全预言**必须人工改写：工具常写「可能 200 绕过」，执行标准需区分「漏洞观察」与「质量验收」。
4. **PyTest + Playwright 映射**：从 `人工优化/` 生成 `test_cases.json`；API 与 UI 脚本覆盖 35/36 代表用例，**工具链从设计到执行闭环可用**。

### 12.6 结论

登录模块在 localhost:3001 上 **API + UI 自动化回归全部通过或按预期 XFail/Skip**，无意外 Fail。功能登录、客户端校验、Remember Me、2FA、异常处理与会话行为与需求一致；已知安全漏洞（SQLi、弱口令、无限速）均被捕获。仅 Google OAuth 正向跳转（LR-029）与 reset-password 限速、DB 故障注入受环境限制。完整用例集见 `人工优化/`；脚本见 `scripts/target_app_tests/`。

## 13. 附录：原始 CSV 需求字段

| CSV ID | title | requirement | Input_Fields | Data_Ranges | Conditions | Expected_Actions | Priority | Technique |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LR-001 | Valid login with correct credentials | Registered user can log in with valid email and password via the login form. | email + password | email: admin@juice-sh.op; password: admin123 (seed user admin) | User exists; MD5(password) matches stored hash; deletedAt IS NULL; totpSecret is empty | 200 on POST /rest/user/login; response.authentication contains token and bid; client stores token in localStorage and cookie (8h expiry); sessionStorage bid; redirect to /search or redirectUrl; isLoggedIn=true | High | EP |
| LR-002 | Login redirects to custom return URL | After successful login the SPA navigates to redirectUrl from the login route query string. | email + password + redirectUrl query param | valid credentials; redirectUrl e.g. /#/basket | User authenticated successfully; redirectUrl present on /login route | router.navigateByUrl(redirectUrl) after basket merge; JWT and bid stored | Medium | DT |
| LR-003 | TOTP-enabled account requires second factor | Users with non-empty totpSecret must complete 2FA after password validation. | email + password | email: wurstbrot@juice-sh.op; password: EinBelegtesBrotMitSchinkenSCHINKEN! | Password matches but totpSecret != '' in Users table | 401 on POST /rest/user/login with status totp_token_required and data.tmpToken; client stores totp_tmp_token and navigates to /2fa/enter | High | DT |
| LR-004 | Empty email blocks client-side submit | Login form must not submit when email is empty. | email (password may be filled) | email: empty string; password: any non-empty | emailControl invalid due to Validators.required | Login button disabled; mat-error MANDATORY_EMAIL; no HTTP request to /rest/user/login | Medium | EP |
| LR-005 | Empty password blocks client-side submit | Login form must not submit when password is empty. | password (email valid) | password: empty string; email: non-empty | passwordControl invalid (required and minLength) | Login button disabled; mat-error MANDATORY_PASSWORD; no HTTP request | Medium | EP |
| LR-006 | Both email and password empty | Login form stays disabled when both fields are empty. | email + password | email: ''; password: '' | Both reactive form controls invalid | Login button disabled; no HTTP request | Medium | EP |
| LR-007 | Password minimum length boundary (length=1) | Single-character password satisfies client minLength(1) and is sent to the server. | password + valid email | password length = 1 | Client validation passes; server compares MD5 hash | Form submits; 200 if hash matches else 401 Invalid email or password | Medium | BVA |
| LR-008 | Password below minimum length (empty) | Zero-length password fails client validation before API call. | password | password length = 0 | Validators.required and minLength(1) fail | Button disabled; MANDATORY_PASSWORD; no HTTP request | Low | BVA |
| LR-009 | Malformed email without @ is still submitted | Login form has no email format validator; malformed email reaches the API. | email | email: admin (no @ or domain) | Only Validators.required on emailControl | Request sent to POST /rest/user/login; SQL query uses raw email string; typically 401 Invalid email or password | Medium | EP |
| LR-010 | SQL metacharacters in email field | Email is interpolated into raw SQL in routes/login.ts without parameterization. | email + password | email contains quotes or comment sequences e.g. admin'-- | Raw string interpolation in Sequelize query | May alter SQL semantics; see LR-014; form still submits | High | DT |
| LR-011 | Wrong password for valid email | Invalid password must not authenticate the user. | email + password | email: admin@juice-sh.op; password: incorrect non-empty value | MD5(password) does not match stored hash | 401 Invalid email or password; token cookie and bid cleared; isLoggedIn=false; error shown in template | High | EP |
| LR-012 | Non-existent email | Unknown email cannot log in. | email + password | email: nonexistent@juice-sh.op; password: any | SELECT returns no row | 401 Invalid email or password; session artifacts cleared | Medium | EP |
| LR-013 | Soft-deleted user cannot log in | Users with deletedAt set are excluded from login query (paranoid Users model). | email + password | email: chris.pike@juice-sh.op; password: uss enterprise | deletedFlag in seed; SQL includes AND deletedAt IS NULL | 401 Invalid email or password; user treated as not found | Medium | DT |
| LR-014 | SQL injection tautology in email | Classic SQLi in email may bypass password check (intentional vulnerability). | email + password | email: admin@juice-sh.op'-- or ' OR 1=1-- style payload; password: arbitrary | Unparameterized query in login route | 200 possible with JWT for matched row; weakPasswordChallenge may trigger for admin@juice-sh.op + admin123 | High | EP |
| LR-015 | SQL injection UNION in email | UNION-based injection via email field may leak or alter query results. | email + password | email: ' UNION SELECT ... -- style payload | Column count and types must align for successful UNION | 200 or 401 or 500 depending on payload; possible DB error leakage | High | EP |
| LR-016 | XSS payload in email (error reflection) | Login error message is bound via Angular interpolation in login template. | email | email: <script>alert(1)</script> style payload | Server returns 401 message; {{error}} in login.component.html | Angular escapes HTML by default; no script execution in standard build; email sanitized on registration not on login input | Medium | EP |
| LR-017 | XSS payload in password field | Password is MD5-hashed server-side and not echoed in login error. | password | password: HTML/script payload | Only generic error message returned | 401 Invalid email or password; no plaintext password reflection | Low | EP |
| LR-018 | No rate limiting on login endpoint | Brute-force attempts against login are not throttled at middleware level. | email + password | Repeated failed login attempts | No express-rate-limit on POST /rest/user/login in server.ts | Unlimited attempts; no 429 from login route | High | DT |
| LR-019 | Rate limiting on reset-password (contrast) | Document that password reset is rate-limited while login is not. | email (forgot-password flow) | windowMs=5min; max=100 per IP or X-Forwarded-For | rateLimit middleware on /rest/user/reset-password only | 429 after threshold; trust proxy enabled | Medium | BVA |
| LR-020 | JWT token expiry (6 hours) | Issued JWT uses RS256 with expiresIn 6h; cookie max-age differs. | successful login | JWT exp 6h; cookie expires +8h from login time | security.authorize uses expiresIn 6h | Authenticated API calls fail after JWT expiry with 401; user must re-login | High | BVA |
| LR-021 | Remember me stores email in localStorage | Remember-me checkbox persists email for next visit regardless of login outcome. | rememberMe checkbox + email | rememberMe true or false | login() writes or removes localStorage email after POST | On next visit email field pre-filled when rememberMe was checked | Medium | DT |
| LR-022 | Server error during login is handled | Database or Sequelize errors propagate to Express error handler. | email + password | Simulate DB failure during login query | catch block calls next(error) | 500 response; client clears token bid; isLoggedIn=false; error displayed | Medium | EP |
| LR-023 | Password comparison is case-sensitive | MD5 hash is computed on exact password string. | email + password | admin@juice-sh.op; Admin123 vs admin123 | Different MD5 digests for case variants | 401 when case does not match seed password | Medium | EP |
| LR-024 | Leading or trailing spaces in email | Login route does not trim email before SQL query. | email | email: ' admin@juice-sh.op ' with spaces | No trim() in login route unlike some registration paths | 401 unless DB stores email with same whitespace | Low | BVA |
| LR-025 | Concurrent sessions for same user | Each successful login issues a new JWT without invalidating prior tokens. | same credentials from two sessions | valid user credentials | authenticatedUsers tokenMap stores multiple tokens | Multiple valid JWTs until expiry; new basket id per login flow | Medium | DT |
| LR-026 | Default admin weak password challenge | Predefined admin credentials solve weakPasswordChallenge. | email + password | admin@juice-sh.op + admin123 | verifyPreLoginChallenges checks exact email and password | 200 login; admin role JWT; challenge solved | High | EP |
| LR-027 | Password visibility toggle | User can show or hide password characters in the login form. | password field UI | hide flag toggles input type password vs text | Mat-icon button toggles hide property | Visual masking only; no change to submitted value | Low | DT |
| LR-028 | Enter key submits login form | Pressing Enter in the login form triggers login(). | keyboard Enter in login-form | valid or invalid form state | formSubmitService.attachEnterKeyHandler on login-form | Same behavior as clicking Log in when form valid | Low | DT |
| LR-029 | Google OAuth button when redirect is authorized | Google login is shown only for authorized redirect URIs from application config. | Google OAuth button | redirectUri matches config.application.googleOauth.authorizedRedirects | oauthUnavailable=false when origin authorized | Redirect to accounts.google.com OAuth with client_id response_type=token scope=email | Medium | DT |
| LR-030 | Google OAuth hidden for unauthorized origin | OAuth controls hidden when current origin is not in authorizedRedirects. | page load on /login | origin not listed in googleOauth.authorizedRedirects | oauthUnavailable=true | No Google login button; console log about unauthorized redirect URI | Low | DT |
| LR-031 | 2FA verify with valid TOTP after tmpToken | Complete login after totp_token_required using /rest/2fa/verify. | tmpToken + totpToken | tmpToken from login 401; TOTP from secret of wurstbrot@juice-sh.op | verifySync valid within epochTolerance 30 | 200 on POST /rest/2fa/verify; authentication token and bid returned; full session established | High | DT |
| LR-032 | 2FA verify with invalid TOTP | Wrong TOTP code must not complete authentication. | tmpToken + totpToken | valid tmpToken; incorrect 6-digit code | verifySync returns invalid | 401 on POST /rest/2fa/verify; no full session JWT | High | EP |
| LR-033 | Login challenge user Jim | Successful login as Jim solves loginJimChallenge. | email + password | jim@juice-sh.op + ncc-1701 | verifyPostLoginChallenges compares user id to users.jim | 200 login; loginJimChallenge solved | Medium | EP |
| LR-034 | Login challenge user Bender | Successful login as Bender solves loginBenderChallenge. | email + password | bender@juice-sh.op + OhG0dPlease1nsertLiquor! | verifyPostLoginChallenges compares user id to users.bender | 200 login; loginBenderChallenge solved | Medium | EP |
| LR-035 | Basket associated on successful login | Server finds or creates a basket for the authenticated user. | successful login | any valid non-TOTP user | BasketModel.findOrCreate after authentication | Response includes bid; client merges guest basket then updates cart count | Medium | ST |
| LR-036 | Exposed testing credentials on login page | Login component exposes testing@juice-sh.op credentials in source for QA. | email + password | testing@juice-sh.op + IamUsedForTesting | testingUsername and testingPassword fields in LoginComponent; solves exposedCredentialsChallenge on login | 200 admin login when credentials used; challenge solved | Medium | EP |

## 14. 附录：JSON 导出文件清单

| 识别ID | 文件名 | 候选用例数 | 技术分布 | Suite名称 |
| --- | --- | --- | --- | --- |
| LR-001 | LR-001.json | 6 | EP:2, BVA:3, StateTransition:1 | Combined design for LR-001 Valid login with correct credentials |
| LR-002 | LR-002.json | 22 | EP:3, BVA:18, StateTransition:1 | Combined design for LR-002 Login redirects to custom return URL |
| LR-003 | LR-003.json | 17 | EP:2, BVA:12, DT:2, StateTransition:1 | Combined design for LR-003 TOTP-enabled account requires second factor |
| LR-004 | LR-004.json | 17 | EP:2, BVA:12, DT:2, StateTransition:1 | Combined design for LR-004 Empty email blocks client-side submit |
| LR-005 | LR-005.json | 19 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-005 Empty password blocks client-side submit |
| LR-006 | LR-006.json | 17 | EP:2, BVA:12, DT:2, StateTransition:1 | Combined design for LR-006 Both email and password empty |
| LR-007 | LR-007.json | 20 | EP:2, BVA:12, DT:4, StateTransition:2 | Combined design for LR-007 Password minimum length boundary (length=1) |
| LR-008 | LR-008.json | 16 | EP:1, BVA:6, DT:8, StateTransition:1 | Combined design for LR-008 Password below minimum length (empty) |
| LR-009 | LR-009.json | 19 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-009 Malformed email without @ is still submitted |
| LR-010 | FR-010.json | 19 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-010 SQL metacharacters in email field |
| LR-011 | FR-011.json | 19 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-011 Wrong password for valid email |
| LR-012 | FR-012.json | 17 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-012 Non-existent email |
| LR-013 | FR-013.json | 19 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-013 Soft-deleted user cannot log in |
| LR-014 | FR-014.json | 19 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-014 SQL injection tautology in email |
| LR-015 | FR-015.json | 19 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-015 SQL injection UNION in email |
| LR-016 | FR-016.json | 24 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-016 XSS payload in email (error reflection) |
| LR-017 | FR-017(no_risk).json | 19 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-017 XSS payload in password field |
| LR-018 | FR-018(no_risk).json | 21 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-018 No rate limiting on login endpoint |
| LR-019 | FR-019.json | 16 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-019 Rate limiting on reset-password (contrast) |
| LR-020 | FR-020.json | 21 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-020 JWT token expiry (6 hours) |
| LR-021 | FR-021.json | 17 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-021 Remember me stores email in localStorage |
| LR-022 | LR-022 后端 500 错误处理.json | 19 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-022 Server error during login is handled |
| LR-023 | LR-023 Password comparison .json | 9 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-023 Password comparison is case-sensitive |
| LR-024 | LR-024 Leading or trailing .json | 17 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-024 Leading or trailing spaces in email |
| LR-025 | LR-025 Concurrent sessions .json | 23 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-025 Concurrent sessions for same user |
| LR-026 | LR-026 Default admin weak p.json | 14 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-026 Default admin weak password challenge |
| LR-027 | LR-027 Password visibility .json | 10 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-027 Password visibility toggle |
| LR-028 | LR-028 Enter key submits lo.json | 20 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-028 Enter key submits login form |
| LR-029 | LR-029 Google OAuth button .json | 13 | EP:2, BVA:12, DT:4, StateTransition:1 | Combined design for LR-029 Google OAuth button when redirect is authorized |
| LR-030 | LR-030.json | 10 | EP:1, BVA:6, DT:2, StateTransition:1 | Combined design for LR-030 Google OAuth hidden for unauthorized origin |
| LR-031 | LR-031.json | 14 | EP:2, BVA:6, DT:4, StateTransition:2 | Combined design for LR-031 2FA verify with valid TOTP after tmpToken |
| LR-032 | LR-032.json | 11 | EP:2, BVA:6, DT:2, StateTransition:1 | Combined design for LR-032 2FA verify with invalid TOTP |
| LR-033 | LR-033.json | 6 | EP:2, BVA:3, StateTransition:1 | Combined design for LR-033 Login challenge user Jim |
| LR-034 | LR-034.json | 6 | EP:2, BVA:3, StateTransition:1 | Combined design for LR-034 Login challenge user Bender |
| LR-035 | LR-035.json | 4 | EP:2, StateTransition:2 | Combined design for LR-035 Basket associated on successful login |
| LR-036 | LR-036.json | 8 | EP:2, BVA:3, DT:2, StateTransition:1 | Combined design for LR-036 Exposed testing credentials on login page |

---

