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
| 文档状态 | **已执行**（2026-05-30）；含 API + UI 自动化结果与分析 |
| 生成日期 | 2026-05-30 |

## 1. 被测对象与测试范围

### 1.1 被测对象

OWASP Juice Shop 是一个故意包含常见 Web 安全问题的教学型电商应用。本次选择登录模块作为目标应用的主要功能模块，测试重点包括账号密码认证、2FA 分支、客户端校验、Token/会话处理、安全输入、速率限制和登录相关 UI 交互。

### 1.2 范围内

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

### 1.3 范围外

- 商品浏览、支付、优惠券和 Deluxe 会员完整性校验（登录成功后的购物车合并行为除外，见 LR-035）。
- Google OAuth 的完整外部授权回调是否成功，受第三方配置和网络环境影响，本文件仅设计并验证按钮可见性与跳转请求参数。
- 2FA 的 setup/disable 管理流程不在本次登录模块主范围；本文件仅覆盖登录过程中的 TOTP 门禁与 `/rest/2fa/verify` 正反向验证。

### 1.4 项目资料与证据来源

| 依据文件/目录 | 本文档使用方式 |
| --- | --- |
| `fixtures/juice-shop/README.md` | 确认 fixtures 目录角色：138 条全应用需求、风险分析报告、综合计划、登录模块详细设计文档和风险登记册。 |
| `fixtures/juice-shop/OWASP_Juice_Shop_风险分析报告.md` 与 `risk_register.csv` | 作为风险背景的可信基线：全应用 138 条需求、39 条 High；用户登录与会话模块平均风险分 17.7，SQL 注入、登录拒绝、输入处理、无登录限速等为高风险。 |
| `fixtures/juice-shop/juice_shop_requirements.csv` | 提供全应用 18 模块、138 条需求的粗粒度背景；登录模块对应 AUTH、PWD、TFA、UI 等条目。 |
| `login_requirements.csv` | 作为登录模块详细设计的 36 条 LR 需求基线。 |
| `人工优化/` | 作为最终详细测试设计集，当前仓库实数为 36 个 CSV、146 条终稿用例。 |
| `scripts/target_app_tests/` | 作为执行证据来源：API 自动化、UI 自动化、测试数据生成与页面对象 helper。 |
| `测试过程与结果索引.md` | 作为测试过程和最终结果的索引；本文档进一步按当前仓库文件重新核对行内数字、状态和来源。 |

## 2. IntelliTest 设计流程

本次测试设计严格对应 IntelliTest 项目规划中的 FR 1.0 至 FR 6.0：

1. **FR 1.0 输入/解析**：将项目登录需求 CSV 转换为逐条自然语言需求输入。
2. **FR 1.1 需求结构化**：抽取输入字段、数据范围、条件和预期动作。
3. **FR 2.0 风险分析**：结合全应用风险报告与登录专项 CSV 风险分，确定执行优先级；SQL 注入、无登录限速、弱口令、暴露凭据等作为高风险优先验证。
4. **FR 3.0 黑盒测试设计**：生成 EP、BVA、DT 候选测试用例。
5. **FR 4.0 白盒建模**：生成 StateTransition 用例和覆盖项，体现登录状态路径。
6. **FR 5.0 测试预言生成**：每条测试用例生成 `expected_result`，作为执行时的 Pass/Fail 判定标准。
7. **FR 6.0 输出导出**：每条需求导出 CSV/JSON 制品，供本文档与自动化脚本汇总。
8. **人工交互审查**：测试设计者筛除不适用候选、补充真实测试数据、重写安全测试预言。

### 2.1 Prompt 设计与工具配置

为保证测试设计可追溯、可复核，并能说明工具生成结果与人工审查之间的关系，本次使用 IntelliTest 时采用如下 Prompt/配置思路：

| 工具阶段 | Prompt/配置目标 | 本次登录模块中的实际使用 |
| --- | --- | --- |
| 需求结构化 Prompt | 从自然语言需求中抽取 `input_fields`、`data_ranges`、`conditions`、`expected_actions` | 将 CSV 每行改写为完整需求文本后输入工具，由大模型抽取邮箱、密码、redirectUrl、TOTP、JWT、Remember Me 等字段 |
| 风险分析 Prompt | 按 Impact × Likelihood 生成风险分数和 High/Medium/Low 优先级 | 对 SQL 注入、弱口令、无速率限制、JWT、2FA 等高风险需求生成或人工补充风险优先级 |
| 黑盒生成配置 | 勾选 EP、BVA、DT，生成候选覆盖项和测试用例 | 对所有需求统一生成候选用例，再由人工筛选出适合登录模块的最终用例 |
| 白盒建模 Prompt | 将需求映射为状态、事件、守卫条件、动作、下一状态 | 生成 LoggedOut、Authenticated、Awaiting2FA、TokenExpired、LoginFailed 等状态迁移路径 |
| 测试预言 Prompt | 基于需求、测试数据和条件合成 `expected_result` | 生成 HTTP 状态、页面跳转、token/cookie/sessionStorage、错误提示和安全期望 |
| 导出配置 | 导出 requirements、test_cases、coverage_items、summary | 每条 LR 导出 CSV；流水线：`未优化/` → `优化/` → **`人工优化/`**（146 条终稿） |

人工审查没有改变工具本身的输出文件，而是在本文档中记录筛选与审查结果：保留有效候选用例、删除无意义 BVA 边界、补充真实 Juice Shop 测试数据，并对 SQL 注入等安全用例重写判定标准。

## 3. 测试设计策略

| 技术 | 使用场景 | 本项目中的应用 |
| --- | --- | --- |
| EP 等价类划分 | 有效/无效输入类别、正常/异常账号 | 合法凭据、错误密码、不存在邮箱、XSS payload、SQL payload、OAuth 配置等 |
| BVA 边界值分析 | 明确长度、次数、时间或开关边界 | 密码长度 0/1、reset-password 100 次阈值、JWT 6h 过期、邮箱前后空格边界 |
| DT 决策表 | 条件组合导致不同动作 | redirectUrl 是否存在、TOTP 是否开启、用户是否软删除、Remember Me true/false、多端登录 |
| StateTransition 状态迁移 | 登录前后状态、失败状态、2FA 等待状态、Token 过期状态 | LoggedOut/Unauthenticated/LoginPage -> LoggedIn/Authenticated/Awaiting2FA/Error 等路径 |
| 测试预言 Oracle | 每条用例的可判定预期 | HTTP 状态、路由跳转、localStorage/cookie/sessionStorage、错误提示、是否签发 JWT |
| 风险驱动排序 | 优先执行高风险安全和认证路径 | SQL 注入、弱口令、无速率限制、JWT、2FA 优先执行 |

## 4. 需求追踪矩阵

说明：本表以 `人工优化/` 当前 CSV 为准重新统计；`专项风险分` 来自终稿用例 CSV 的 `risk_score` 字段，风险背景与优先级解释参照 `OWASP_Juice_Shop_风险分析报告.md`。`终稿状态` 是设计阶段可执行性标记，最终执行结论见 §10。

| CSV ID | 需求标题 | 类别 | 优先级 | 建议方法 | 专项风险分 | 终稿用例 | 终稿技术构成 | 终稿状态 |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| LR-001 | 正确凭据登录 | 正常登录 | High | EP | 15 | 5 | EP×3, DT×1, ST×1 | satisfied |
| LR-002 | 登录后跳转到自定义返回地址 | 正常登录 | Medium | DT | 16 | 4 | EP×1, DT×2, ST×1 | satisfied |
| LR-003 | 开启 TOTP 的账号登录 | 二次认证 | High | DT | 15 | 5 | EP×1, DT×2, ST×2 | satisfied |
| LR-004 | 邮箱为空校验 | 输入校验 | Medium | EP | 6 | 4 | EP×1, DT×2, ST×1 | ui_only |
| LR-005 | 密码为空校验 | 输入校验 | Medium | EP | 9 | 3 | EP×1, DT×1, ST×1 | ui_only |
| LR-006 | 邮箱和密码同时为空校验 | 输入校验 | Medium | EP | 6 | 3 | EP×1, DT×1, ST×1 | ui_only |
| LR-007 | 密码最小长度边界值 | 输入校验 | Medium | BVA | 20 | 6 | EP×2, BVA×2, DT×1, ST×1 | satisfied |
| LR-008 | 密码低于最小长度边界值 | 输入校验 | Low | BVA | 9 | 4 | EP×1, BVA×1, DT×1, ST×1 | ui_only |
| LR-009 | 不含 @ 的邮箱格式输入 | 输入校验 | Medium | EP | 12 | 3 | EP×1, DT×1, ST×1 | satisfied |
| LR-010 | 邮箱字段包含 SQL 特殊字符 | 安全输入 | High | DT | 25 | 3 | EP×1, DT×1, ST×1 | satisfied |
| LR-011 | 正确邮箱错误密码登录 | 异常登录 | High | EP | 10 | 3 | EP×1, DT×1, ST×1 | satisfied |
| LR-012 | 不存在邮箱登录 | 异常登录 | Medium | EP | 10 | 3 | EP×1, DT×1, ST×1 | satisfied |
| LR-013 | 软删除用户登录 | 异常登录 | Medium | DT | 12 | 4 | EP×1, DT×2, ST×1 | satisfied |
| LR-014 | 邮箱字段 SQL 注入恒真绕过 | 安全测试 | High | EP | 25 | 4 | EP×2, DT×1, ST×1 | satisfied |
| LR-015 | 邮箱字段 Union SQL 注入 | 安全测试 | High | EP | 12 | 4 | EP×2, DT×1, ST×1 | satisfied |
| LR-016 | 邮箱字段 XSS 输入 | 安全测试 | Medium | EP | 6 | 5 | EP×2, DT×2, ST×1 | satisfied |
| LR-017 | 密码字段 XSS 输入 | 安全测试 | Low | EP | 15 | 3 | EP×1, DT×1, ST×1 | satisfied |
| LR-018 | 登录接口速率限制 | 安全测试 | High | DT | 20 | 4 | EP×2, DT×1, ST×1 | satisfied |
| LR-019 | 忘记密码接口速率限制对照 | 关联认证功能 | Medium | BVA | 12 | 7 | EP×2, BVA×2, DT×2, ST×1 | blocked |
| LR-020 | JWT Token 过期 | 会话与 Token | High | BVA | 15 | 6 | EP×3, DT×2, ST×1 | satisfied |
| LR-021 | Remember Me 邮箱记忆 | 会话与 Token | Medium | DT | 9 | 4 | EP×1, DT×2, ST×1 | ui_only |
| LR-022 | 后端 500 错误处理 | 异常处理 | Medium | EP | 16 | 4 | EP×2, DT×1, ST×1 | blocked |
| LR-023 | 密码大小写敏感 | 输入校验 | Medium | EP | 20 | 3 | EP×1, DT×1, ST×1 | satisfied |
| LR-024 | 邮箱前后空格处理 | 输入校验 | Low | BVA | 9 | 5 | EP×1, BVA×2, DT×1, ST×1 | satisfied |
| LR-025 | 同一用户多端并发登录 | 会话与 Token | Medium | DT | 20 | 3 | EP×1, DT×1, ST×1 | satisfied |
| LR-026 | 默认管理员弱口令 | 安全测试 | High | EP | 12 | 4 | EP×1, DT×2, ST×1 | satisfied |
| LR-027 | 密码显示隐藏切换 | UI 交互 | Low | DT | 6 | 4 | EP×2, DT×1, ST×1 | ui_only |
| LR-028 | 登录表单回车提交 | UI 交互 | Low | DT | 4 | 5 | EP×2, DT×2, ST×1 | ui_only |
| LR-029 | Google OAuth 登录跳转 | 第三方登录 | Medium | DT | 12 | 5 | EP×2, DT×2, ST×1 | satisfied（执行时因按钮未渲染 Skip） |
| LR-030 | 未授权来源隐藏 OAuth | 第三方登录 | Low | DT | 12 | 3 | EP×1, DT×1, ST×1 | ui_only（Playwright 已验证 oauthUnavailable 下按钮隐藏 Pass） |
| LR-031 | 2FA 有效 TOTP 验证 | 二次认证 | High | DT | 20 | 4 | EP×1, DT×2, ST×1 | satisfied |
| LR-032 | 2FA 无效 TOTP 验证 | 二次认证 | High | EP | 15 | 4 | EP×2, DT×1, ST×1 | satisfied |
| LR-033 | Jim 挑战用户登录 | 正常登录 | Medium | EP | 6 | 3 | EP×1, DT×1, ST×1 | satisfied |
| LR-034 | Bender 挑战用户登录 | 正常登录 | Medium | EP | 4 | 3 | EP×1, DT×1, ST×1 | satisfied |
| LR-035 | 登录关联 Basket | 会话与 Token | Medium | ST | 12 | 6 | EP×3, DT×2, ST×1 | satisfied |
| LR-036 | 页面暴露 testing 凭据 | 安全测试 | Medium | EP | 25 | 3 | EP×1, DT×1, ST×1 | satisfied |

## 5. 工具生成结果摘要

### 5.1 用例流水线统计

| 阶段 | 目录/来源 | 用例数 | 技术分布（约） | 说明 |
| --- | --- | ---: | --- | --- |
| 综合流程原始导出 | `未优化/` | **138** | EP/BVA/DT/ST | LLM 黑盒 + 白盒 ST，2026-05-29 重跑 |
| 套件脚本优化中间稿 | `优化/` | **135** | EP:46, BVA:4, DT:47, ST:38 | 当前仓库实数；中间目录仅作过程参考，不作为最终设计基线 |
| 人工审查终稿 | `人工优化/` | **146** | EP:53, BVA:7, DT:49, ST:37 | 当前设计基线；含 `precondition_status` 与 `execution_note` |
| 代表执行用例 | 本文档 §6 | **36** | 每 LR 1 条 TC-* | 与 §10 执行结果一一对应 |
| API 自动化 | `test_login_api.py` | **30** 项 | 27 Pass / 2 Skip / 1 XFail | 2026-05-30；含 LR-007/LR-020 辅助断言与 traceability 检查 |
| UI 自动化 | `test_login_ui.py` | **9** 项 | 8 Pass / 1 Skip | 2026-05-30 Playwright |

设计原则：保留能直接验证登录行为的 EP/BVA/DT/ST 多技术用例；对安全用例进行预言改写；筛除无意义通用数值 BVA；终稿不压缩为「每需求 1 条」，以 `人工优化/` 146 条为完整设计集，§6 代表用例用于执行记录与脚本映射。本文后续所有统计均以当前仓库 CSV 实数为准。

### 5.2 AI 原始候选用例示例与处理

| CSV ID | 原始生成用例ID | 技术 | 原始标题 | 原始数据 | 原始预期 | 人工处理 | 处理说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LR-001 | LR-001_EP_001 | EP | Valid login with correct email and password | user@example.com 占位账号 | 成功登录 | 保留/修正 | 替换为 `admin@juice-sh.op / admin123`，补 token、bid、redirect 断言。 |
| LR-001 | tc-st-fd9556f1 | StateTransition | LoggedOut -> LoggedIn | login | 登录后进入 LoggedIn | 保留/修正 | 与 EP 正向路径合并为代表用例 TC-LOGIN-001。 |
| LR-003 | LR-003_EP_001 | EP | Valid password, non-empty totpSecret triggers 2FA | correct_password 占位 | 需要二次认证 | 保留/修正 | 替换为 `wurstbrot@juice-sh.op` 种子账号，断言 `totp_token_required` 与 tmpToken。 |
| LR-014 | LR-014_EP_002 | EP | SQL injection email bypasses authentication | `' OR 1=1 --` | 登录绕过成功 | 人工改写 | 将漏洞观察改为安全验收预言：应 401；若 200+JWT 记录 DEF-001。 |
| LR-014 | LR-014_DT_001 | DT | SQL injection bypass rule | SQLi 条件为真 | 绕过密码校验 | 人工改写 | 保留决策表覆盖，补 Juice Shop 可执行 payload。 |
| LR-014 | SUP-LR-014-EP-003 | EP | OR 1=1-- payload | `' OR 1=1--` | 应拒绝登录 | 人工补漏 | 因 `login_requirements.csv` Data_Ranges 明确两类 SQLi payload，补第二类。 |
| LR-018 | LR-018_EP_001 | EP | Brute-force login attempts not throttled | requests: 100 | 不限速 | 人工改写 | 将测试脚本收敛为多次错误登录，观察是否出现 429。 |
| LR-019 | MAN-LR-019-BVA-001/002 | BVA | reset-password 第 100/101 次边界 | 100/101 requests | 101 次后 429 | 人工补漏 | 保留边界设计；实际执行因 localhost reset-password 全 500 而 Skip。 |
| LR-020 | LR-020_EP_003 / LR-020_DT_001 | EP/DT | JWT 6h expiry and cookie mismatch | token/cookie | 过期后 401 | 保留/修正 | 剔除需要改服务端配置的候选，执行阶段用有效/无效 token 验证核心 oracle。 |
| LR-027 | LR-027_DT_001 / MAN-LR-027-EP-001 | DT/EP | 密码显示隐藏切换 | password field | password/text 切换 | 保留/补漏 | 用 Playwright 直接验证 UI 控件行为。 |

### 5.3 人工审查与修改记录

| 修改ID | 涉及需求 | 人工操作 | 修改内容 | 理由 |
| --- | --- | --- | --- | --- |
| MR-001 | LR-001/LR-002/LR-003 | 补充具体账号与路径 | 工具原始用例多使用 valid_input，人工替换为 Juice Shop 可执行数据，如 admin@juice-sh.op、admin123、/#/basket、wurstbrot@juice-sh.op。 | 提升可执行性和可复现性。 |
| MR-002 | 多条 BVA 候选 | 筛除无效通用边界 | 对无明确数值边界的 email/password/redirectUrl 候选不纳入代表执行表；仅保留 LR-007、LR-008、LR-019、LR-024 等真实边界。 | 满足人工审查要求，避免无意义用例污染执行。 |
| MR-003 | LR-014/LR-015 | 重写安全预言 | CSV 中记录“可能 200 绕过”的观察结果，人工改为“安全期望应拒绝认证；若 200 则记录高危缺陷”。 | 区分漏洞复现观察与质量验收标准。 |
| MR-004 | LR-018 | 补充暴力破解执行策略 | 由于登录接口无速率限制，人工将 DT 候选改写为连续请求验证，并要求记录 429/锁定策略是否存在。 | 让风险测试可执行、可取证。 |
| MR-005 | LR-020 | 补充可执行替代方案 | JWT 6 小时等待成本高，人工允许使用测试环境短时配置、模拟过期 token 或调整时间进行验证。 | 降低执行成本，同时保持测试目标一致。 |
| MR-006 | LR-029/LR-030 | 标记外部依赖并在执行阶段校准 | Google OAuth 正向跳转依赖 authorizedRedirects；本次 localhost 实际未渲染 Google 按钮，故 LR-029 Skip、LR-030 隐藏逻辑 Pass。 | 避免将环境未满足误判为功能失败。 |
| MR-007 | LR-031/LR-032 | 补充 2FA 完整路径 | 在 LR-003 密码验证基础上，人工补充 `/rest/2fa/verify` 的正向与负向用例及 TOTP 数据。 | 覆盖二次认证完成登录的完整需求。 |
| MR-008 | LR-033~LR-036 | 补充挑战账号与 Basket 断言 | 为 Jim、Bender、testing 账号补充种子凭据；LR-035 在登录响应中断言 bid，游客购物车合并保留为设计覆盖点。 | 对齐 Juice Shop 种子数据与登录后会话行为；本轮自动化未完整验证游客购物车商品合并。 |

## 6. 最终详细测试用例与执行表

说明：`人工优化/` 共 **146** 条终稿用例（36 个 CSV 文件）；本章列出 **36 条代表用例**（TC-*），与 §10 执行结果对应。`来源用例` 列列出代表用例主要映射到的终稿 `test_case_id`，完整追溯见 `人工优化/LR-*.csv`。

**代表用例执行摘要（2026-05-30，http://localhost:3001）**：36 条代表用例中 **32 Pass**、**3 Skip**、**1 XFail**。自动化测试项层面为 **39 项：35 Passed、3 Skipped、1 XFailed、0 Failed**。差异原因是 LR-007、LR-020 和 traceability 检查包含额外自动化断言。

| 用例ID | LR | 技术/风险 | 来源用例 | 测试数据 | 执行步骤与测试预言 | 执行状态 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-LOGIN-001 | LR-001 正确凭据登录 | EP + ST / 15 | LR-001_EP_001, LR-001_DT_001, tc-st-fd9556f1 | admin@juice-sh.op / admin123 | 提交正确账号密码；预期 200、token、bid、登录态建立并跳转。 | **Pass** |
| TC-LOGIN-002 | LR-002 自定义返回地址 | DT + ST / 16 | LR-002_DT_001, SUP-LR-002-DT-003, tc-st-8d45ba38 | admin@juice-sh.op / admin123；redirectUrl=/#/basket | 设计目标为登录成功后按 redirectUrl 进入目标路由；本轮自动化已验证登录 API 返回 200 与 token。 | **Pass（API 部分）**；redirectUrl UI 跳转待补测 |
| TC-LOGIN-003 | LR-003 TOTP 账号登录 | DT + ST / 15 | LR-003_EP_001, LR-003_DT_002, tc-st-df8324e0 | wurstbrot@juice-sh.op / EinBelegtesBrotMitSchinkenSCHINKEN! | 密码正确但账号启用 TOTP；预期 401、`totp_token_required`、tmpToken。 | **Pass** |
| TC-VAL-004 | LR-004 邮箱为空 | EP / 6 | LR-004_EP_001, LR-004_DT_001, tc-st-d3982c78 | email=""；password=任意非空 | UI 保持按钮 disabled；显示 MANDATORY_EMAIL；不发送登录请求。 | **Pass** |
| TC-VAL-005 | LR-005 密码为空 | EP / 9 | LR-005_EP_001, LR-005_DT_001, tc-st-b591f6d8 | email=合法格式；password="" | UI 保持按钮 disabled；显示 MANDATORY_PASSWORD；不发送登录请求。 | **Pass** |
| TC-VAL-006 | LR-006 双空输入 | EP / 6 | LR-006_EP_001, LR-006_DT_001, tc-st-b5e6d19a | email=""；password="" | 两个控件 invalid；按钮 disabled；无 `/rest/user/login` 请求。 | **Pass** |
| TC-BVA-007 | LR-007 密码长度 1 | BVA / 20 | LR-007_BVA_001, LR-007_EP_001, tc-st-a9abdd9a | lr007test@juice-sh.op / a；admin@juice-sh.op / a | 长度 1 应允许提交；匹配账号 200，不匹配账号 401。 | **Pass** |
| TC-BVA-008 | LR-008 密码长度 0 | BVA / 9 | LR-008_BVA_001, LR-008_EP_001, tc-st-4501235c | password="" | 空密码在客户端被拦截；按钮 disabled；无 API 请求。 | **Pass** |
| TC-VAL-009 | LR-009 邮箱不含 @ | EP / 12 | LR-009_EP_001, LR-009_DT_001, tc-st-8a95bccb | email=admin；password=任意非空 | 前端仅 required 校验，允许提交；服务端返回 401，不产生 token。 | **Pass** |
| TC-SEC-010 | LR-010 SQL 特殊字符 | DT + Security / 25 | LR-010_EP_002, LR-010_DT_001, tc-st-c1e97732 | email=admin'--；password=irrelevant | 输入 SQL 注释符；预期不得认证成功、不得泄露 SQL 错误。 | **Pass** |
| TC-NEG-011 | LR-011 正确邮箱错误密码 | EP + DT / 10 | LR-011_EP_001, LR-011_DT_001, tc-st-fd5b3afe | admin@juice-sh.op / WrongPass123! | 服务端应返回 401；token、cookie、bid 不应建立。 | **Pass** |
| TC-NEG-012 | LR-012 不存在邮箱 | EP / 10 | LR-012_EP_001, LR-012_DT_001, tc-st-4d73c3b9 | nonexistent@juice-sh.op / anything | 未知邮箱登录；预期 401，无 token/bid。 | **Pass** |
| TC-NEG-013 | LR-013 软删除用户 | DT / 12 | LR-013_EP_001, LR-013_DT_001, tc-st-0743a9a5 | chris.pike@juice-sh.op / uss enterprise | 软删除用户被 `deletedAt IS NULL` 排除；预期 401。 | **Pass** |
| TC-SEC-014 | LR-014 SQLi 恒真绕过 | EP + Security / 25 | LR-014_EP_002, LR-014_DT_001, SUP-LR-014-EP-003, tc-st-35016a48 | admin@juice-sh.op'-- / anything | 安全期望为 401 且无 JWT；若 200+JWT 则记录 Critical SQLi 缺陷。 | **XFail**（200+JWT，DEF-001） |
| TC-SEC-015 | LR-015 Union SQLi | EP + Security / 12 | LR-015_EP_002, LR-015_DT_001, SUP-LR-015-EP-003, tc-st-77349c66 | `' UNION SELECT * FROM Users--` / anything | 观察 200/401/500；本轮自动化主要验证 500 响应中不得泄露 SQLite 结构，未单独断言 JWT 签发。 | **Pass** |
| TC-SEC-016 | LR-016 邮箱 XSS | EP + DT / 6 | LR-016_EP_001, SUP-LR-016-EP-002, SUP-LR-016-DT-001, tc-st-ed53ad8c | `<script>alert(1)</script>` / 任意密码 | 错误提示应被 Angular 转义；不得弹窗或 DOM 注入。 | **Pass** |
| TC-SEC-017 | LR-017 密码 XSS | EP / 15 | LR-017_EP_001, LR-017_DT_001, tc-st-eebc1d35 | password=`<img src=x onerror=alert(1)>` | 密码不应明文反射；返回 401；不得执行脚本。 | **Pass** |
| TC-SEC-018 | LR-018 登录无限速 | DT + Security / 20 | LR-018_EP_001, LR-018_DT_001, SUP-LR-018-EP-001, tc-st-7273c39f | 同一 IP 多次错误登录 | 多次错误登录均为认证响应；若无 429/锁定，则记录无登录限速风险。 | **Pass**（RISK-001） |
| TC-REL-019 | LR-019 reset-password 限速 | BVA / 12 | LR-019_DT_001, MAN-LR-019-BVA-001, MAN-LR-019-BVA-002, tc-st-2f90d50c | `/rest/user/reset-password`；100/101 次边界 | 设计预期第 101 次返回 429；本地全部 500，无法验证限速分支。 | **Skip** |
| TC-TOKEN-020 | LR-020 JWT 过期 | BVA + ST / 15 | LR-020_EP_003, LR-020_DT_001, tc-st-b7d627f8 | 有效 JWT、无效/过期 JWT | 有效 token 调 whoami 200；无效 token 401；6h 实等未执行。 | **Pass**（部分替代验证） |
| TC-SESSION-021 | LR-021 Remember Me | DT / 9 | LR-021_EP_001, LR-021_DT_001, SUP-LR-021-DT-003, tc-st-fd573b90 | rememberMe=true；email=任意输入 | 勾选后写入 localStorage.email；重新打开登录页自动回填。 | **Pass** |
| TC-ERR-022 | LR-022 后端 500 | EP + ST / 16 | LR-022_EP_001, MAN-LR-022-EP-001, tc-st-12841f0c | DB/Sequelize 故障注入 | 设计预期 500 后清 token/bid 并显示错误；本次未做 DB 故障注入。 | **Skip** |
| TC-VAL-023 | LR-023 密码大小写敏感 | EP / 20 | LR-023_EP_001, LR-023_DT_001, tc-st-150c4561 | admin@juice-sh.op / Admin123 | 密码大小写不同，MD5 不匹配；预期 401。 | **Pass** |
| TC-VAL-024 | LR-024 邮箱前后空格 | BVA / 9 | LR-024_EP_003, SUP-LR-024-BVA-001, SUP-LR-024-BVA-002, tc-st-2cc76493 | `" admin@juice-sh.op "` / admin123 | 登录路由不 trim；预期 401，不应匹配真实 admin 邮箱。 | **Pass** |
| TC-SESSION-025 | LR-025 多端并发登录 | DT + ST / 20 | LR-025_EP_001, LR-025_DT_001, tc-st-2aa03cdb | 同一账号两个会话 | 两次登录均 200；两个 token 均可独立访问 whoami。 | **Pass** |
| TC-SEC-026 | LR-026 默认管理员弱口令 | EP + Security / 12 | LR-026_EP_001, LR-026_DT_001, tc-st-56893a1c | admin@juice-sh.op / admin123 | 默认凭据可登录且 role=admin；从真实系统角度记录弱口令风险。 | **Pass**（RISK-002） |
| TC-UI-027 | LR-027 密码显示隐藏 | DT / 6 | LR-027_DT_001, MAN-LR-027-EP-001, tc-st-f31f9fa7 | 密码输入框与眼睛按钮 | 点击后 input type 在 password/text 间切换，不影响提交值。 | **Pass** |
| TC-UI-028 | LR-028 Enter 提交 | DT + ST / 4 | LR-028_EP_001, LR-028_DT_001, MAN-LR-028-EP-001, tc-st-4586de66 | 登录表单内按 Enter | Enter 触发与点击 Log in 等价的登录动作。 | **Pass** |
| TC-OAUTH-029 | LR-029 Google OAuth 跳转 | DT / 12 | LR-029_EP_001, LR-029_DT_001, LR-029_DT_002, tc-st-857e838e | Google OAuth 按钮；授权 origin | 正向设计要求按钮存在并跳转 accounts.google.com；localhost 未渲染按钮。 | **Skip** |
| TC-OAUTH-030 | LR-030 未授权来源隐藏 OAuth | DT / 12 | LR-030_EP_001, LR-030_DT_001, tc-st-e6d44d76 | 当前 localhost 登录页 | 在 oauthUnavailable 环境下 Google 按钮不可见。 | **Pass** |
| TC-2FA-031 | LR-031 有效 TOTP | DT + ST / 20 | LR-031_EP_001, LR-031_DT_001, LR-031_DT_004, tc-st-e71130d5 | tmpToken + 有效 TOTP | 先获取 tmpToken，再 POST `/rest/2fa/verify`；预期 200 + token + bid。 | **Pass** |
| TC-2FA-032 | LR-032 无效 TOTP | EP / 15 | LR-032_EP_001, LR-032_EP_002, LR-032_DT_001, tc-st-9df29845 | tmpToken + 000000 | 无效 TOTP 不得签发完整 JWT；预期 401。 | **Pass** |
| TC-CHAL-033 | LR-033 Jim 挑战用户 | EP / 6 | LR-033_EP_001, LR-033_DT_001, tc-st-33d403cf | jim@juice-sh.op / ncc-1701 | Jim 种子账号登录；预期 200，挑战可观测时被解决。 | **Pass** |
| TC-CHAL-034 | LR-034 Bender 挑战用户 | EP / 4 | LR-034_EP_001, LR-034_DT_001, tc-st-1beb6158 | bender@juice-sh.op / OhG0dPlease1nsertLiquor! | Bender 种子账号登录；预期 200。 | **Pass** |
| TC-SESSION-035 | LR-035 Basket 关联 | ST / 12 | LR-035_EP_001, LR-035_DT_001, SUP-LR-035-EP-001, tc-st-7a5188bd | admin@juice-sh.op / admin123 | 成功登录响应应包含 `authentication.bid`；游客购物车合并属于设计覆盖点，本轮自动化未完整验证商品合并流程。 | **Pass（bid 已验证）** |
| TC-SEC-036 | LR-036 testing 凭据暴露 | EP / 25 | LR-036_EP_001, LR-036_DT_001, tc-st-5c311cbd | testing@juice-sh.op / IamUsedForTesting | 前端硬编码测试凭据可登录 admin；记录暴露凭据风险。 | **Pass**（RISK-003） |

## 7. 白盒状态迁移建模结果

以下为 `人工优化/` 当前保留的白盒状态迁移建模摘要。它们不是源代码级语句覆盖，而是面向登录行为的状态迁移模型，用来覆盖登录前后、2FA、失败、令牌、OAuth 与风险路径。完整原始状态迁移用例见各 `人工优化/LR-*.csv` 中 `technique=StateTransition` 的行；若原始 ST 描述与人工安全预言冲突，执行判定以 §6 和 §10 的人工审查预言为准。

| 覆盖主题 | 关联 LR | 当前 ST 用例ID | 关键状态/迁移 | 执行验证 |
| --- | --- | --- | --- | --- |
| 成功登录建会话 | LR-001 | tc-st-fd9556f1 | LoggedOut --valid login--> LoggedIn | TC-LOGIN-001 Pass |
| 登录后重定向 | LR-002 | tc-st-8d45ba38 | LoginPage --login with redirectUrl--> Redirected | TC-LOGIN-002 API 部分 Pass；redirectUrl 页面跳转待 UI 补测 |
| 密码正确但需 2FA | LR-003 | tc-st-df8324e0 | AwaitingPassword --password valid + totpSecret--> Awaiting2FA | TC-LOGIN-003 Pass |
| 客户端表单阻断 | LR-004～008 | tc-st-d3982c78 / tc-st-b591f6d8 / tc-st-b5e6d19a / tc-st-a9abdd9a / tc-st-4501235c | 无效表单保持 disabled；有效边界允许提交 | TC-VAL/BVA-004～008 Pass |
| 服务端拒绝登录 | LR-011～013 | tc-st-fd5b3afe / tc-st-4d73c3b9 / tc-st-0743a9a5 | Unauthenticated --invalid/unknown/deleted user--> Unauthenticated | TC-NEG-011～013 Pass |
| SQL 注入绕过 | LR-014 | tc-st-35016a48 | NotLoggedIn --SQLi payload--> LoggedIn | TC-SEC-014 XFail，记录 DEF-001 |
| 登录无限速 | LR-018 | tc-st-7273c39f | Idle --login_attempt--> Authenticating，无 throttle 分支 | TC-SEC-018 Pass，记录 RISK-001 |
| reset-password 限速对照 | LR-019 | tc-st-2f90d50c | PasswordResetRequested 应进入限速分支；LoginRequested 不限速 | TC-REL-019 Skip，localhost 全 500 |
| JWT 生命周期 | LR-020 | tc-st-b7d627f8 | NoJWT --issueJWT--> JWTIssued；6h 过期后应 401 | TC-TOKEN-020 Pass（替代验证） |
| Remember Me | LR-021 | tc-st-fd573b90 | EmailNotPersisted --remember_me_checked--> EmailPersisted | TC-SESSION-021 Pass |
| 后端错误处理 | LR-022 | tc-st-12841f0c | Processing --DB/Sequelize error--> ErrorHandling | TC-ERR-022 Skip，未做故障注入 |
| 多端会话 | LR-025 | tc-st-2aa03cdb | Active --repeat login--> Active；旧 token 不失效 | TC-SESSION-025 Pass |
| OAuth 显示/隐藏 | LR-029～030 | tc-st-857e838e / tc-st-e6d44d76 | authorized origin 显示；unauthorized/oauthUnavailable 隐藏 | LR-029 Skip；LR-030 Pass |
| 2FA verify | LR-031～032 | tc-st-e71130d5 / tc-st-9df29845 | AwaitingTOTP --valid--> LoggedIn；invalid 留在 AwaitingTOTP | TC-2FA-031/032 Pass |
| Basket 关联 | LR-035 | tc-st-7a5188bd | NoBasket --authenticated login--> BasketExists | TC-SESSION-035 已验证登录响应 bid；游客购物车商品合并待补测 |

## 8. 测试预言设计

测试预言来自 IntelliTest 综合设计导出的 CSV/JSON 中每条测试用例的 `expected_result` 字段，最终以 `人工优化/` CSV 中经人工审查后的文本为准。人工审查时将其分为两类：

- **功能性预言**：例如成功登录后跳转、token 写入、按钮禁用、错误提示显示。
- **安全性预言**：例如 SQL 注入不应绕过认证、XSS 不应执行、暴力破解应受限制。对于 Juice Shop 这种故意含漏洞的目标应用，安全性预言同时记录“真实系统期望”和“若漏洞复现则判定风险/缺陷”。

| 最终用例ID | CSV ID | 技术 | 测试数据 | 最终测试预言 | 来源说明 |
| --- | --- | --- | --- | --- | --- |
| TC-LOGIN-001 | LR-001 | EP + StateTransition | admin@juice-sh.op / admin123 | 返回 200；跳转到 /#/search 或 redirectUrl；localStorage/cookie 存在 token；sessionStorage 存在 bid；isLoggedIn=true。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |
| TC-LOGIN-003 | LR-003 | DT + StateTransition | wurstbrot@juice-sh.op / EinBelegtesBrotMitSchinkenSCHINKEN! | 返回 401 且响应包含 totp_token_required 和 tmpToken；localStorage 写入 totp_tmp_token；页面跳转 /2fa/enter。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |
| TC-SEC-014 | LR-014 | EP + Security | email="admin@juice-sh.op'--" 或 "' OR 1=1--"；password=anything | 安全期望：返回 401 或被安全过滤，不应绕过认证；若 200 登录成功，判定高危 SQL 注入缺陷。 | 工具生成漏洞观察，人工改写为安全验收预言；执行时用 xfail 记录已知靶场漏洞 |
| TC-SEC-018 | LR-018 | DT + Security | 同一 IP 连续多次 POST /rest/user/login | 若无 429 且可无限尝试，记录为高风险；真实系统安全期望是限制频率或触发锁定/验证码。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |
| TC-TOKEN-020 | LR-020 | BVA + StateTransition | 登录后取得 JWT；等待 6h 或模拟过期 token | JWT 验证失败返回 401；Cookie 可能仍存在但无效；用户需要重新登录。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |
| TC-2FA-031 | LR-031 | DT + StateTransition | tmpToken + 有效 totpToken | 返回 200；响应含 authentication.token 与 bid；完成完整登录会话。 | 人工设计，基于 LR-003 后续 verify 路径 |
| TC-SEC-036 | LR-036 | EP | testing@juice-sh.op / IamUsedForTesting | 返回 200；admin 角色 JWT；exposedCredentialsChallenge 被解决。 | 人工设计，对齐 LoginComponent 内嵌测试凭据 |
| TC-UI-027 | LR-027 | DT | 密码输入框与显示/隐藏按钮 | input type 在 password/text 间切换；功能不影响登录提交。 | 由综合设计 expected_result 生成，人工审查后用于 Pass/Fail 判定 |

## 9. 执行环境与测试工具实现

| 项目 | 配置 |
| --- | --- |
| 目标应用 | OWASP Juice Shop，Docker Compose 本地部署 |
| 访问地址 | http://localhost:3001 |
| 执行日期 | 2026-05-30 |
| Python 环境 | Python 3.11 + PyTest 8.x |
| HTTP 客户端 | Requests（`JuiceShopClient`） |
| 2FA | pyotp（wurstbrot TOTP 密钥） |
| 前置账号 | admin、wurstbrot、jim、bender、testing、chris.pike(软删)、lr007test@/a（LR-007 注册） |
| 证据 | PyTest `-v` 控制台输出；可重跑 API 与 UI 全量命令（见 10.1） |

### 9.1 脚本结构与映射

```
scripts/target_app_tests/
├── build_test_cases.py      # 从 人工优化/ 生成 test_cases.json（146 条）
├── conftest.py              # 读取 人工优化/ CSV，提供 client / optimized_cases fixture
├── juice_shop_client.py     # REST 封装：login / verify_2fa / whoami / reset_password
├── test_login_api.py        # API 侧代表用例自动化（30 个测试项）
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

### 9.2 用例类型与实现方式

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

## 10. 执行结果记录

**执行人**：IntelliTest 自动化（PyTest + Playwright）  
**执行环境**：http://localhost:3001  
**执行命令**：`python -m pytest scripts/target_app_tests/test_login_api.py scripts/target_app_tests/test_login_ui.py -v`  
**汇总**：39 项 → **35 Passed**，**3 Skipped**，**1 XFailed**，**0 Failed**（约 27s）

| 用例ID | 执行日期 | 实际结果 | 结论 | 缺陷/风险编号 | 证据 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-LOGIN-001 | 2026-05-30 | POST login 200；含 token 与 bid | **Pass** | — | test_lr001_valid_login | API 层验证 |
| TC-LOGIN-002 | 2026-05-30 | 登录 200，token 有效 | **Pass（API 部分）** | — | test_lr002_login_success_for_redirect_flow | redirectUrl 跳转需 UI 补测 |
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
| TC-SEC-015 | 2026-05-30 | Union payload → 200/401/500，无 sqlite 泄露 | **Pass** | — | test_lr015_sqli_union | 未单独断言 JWT 是否签发 |
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
| TC-SESSION-035 | 2026-05-30 | 登录响应 bid>0 | **Pass（bid 已验证）** | — | test_lr035_basket_id_on_login | 未自动化验证游客购物车商品合并 |
| TC-SEC-036 | 2026-05-30 | testing → 200，role=admin | **Pass** | **RISK-003** 暴露凭据 | test_lr036_testing_credentials | 故意挑战 |
| — | 2026-05-30 | 146 条终稿 oracle 追溯 | **Pass** | — | test_optimized_case_traceability | 批量元数据校验 |

## 11. 测试结果分析

### 11.1 执行统计

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
| 代表用例状态 | 32 Pass + 3 Skip + 1 XFail | 36 条 TC-* 需求代表用例 |
| 预期应通过项通过率 | 35/35 = **100%** | 不含 3 Skip 与 1 XFail |
| 自动化回归异常失败数 | **0** | 无 unexpected Failed；XFail 作为已知靶场漏洞单列管理 |
| 需求记录覆盖 | **36/36** | 每条 LR 均有设计、执行记录或阻塞原因；功能性未完成验证为 LR-019、LR-022、LR-029 |

### 11.2 测试覆盖范围说明

**黑盒技术**（AutoTestDesign LLM 黑盒 + 人工审查）：

- **EP（等价类）**：正常/异常登录、错误密码、不存在用户、XSS、弱口令等（53 条终稿）。
- **BVA（边界值）**：密码长度 0/1、邮箱空格、reset-password 第 100/101 次阈值（7 条）。
- **DT（决策表）**：TOTP 分支、SQLi 条件组合、Remember Me、OAuth 可见性（49 条）。

**白盒技术**：

- **StateTransition（状态迁移）**：综合流程生成并人工保留的 ST 用例 37 条，覆盖 LoggedOut→LoggedIn、Awaiting2FA、FormInvalid、JWTIssued、OAuthHidden 等路径（见 §7）。

**覆盖结论**：36/36 需求在设计上均有终稿用例；39 个自动化项中 35 Passed、1 XFailed、3 Skipped，0 unexpected Failed。LR-004～008、LR-021、LR-027、LR-028、LR-030 已由 Playwright 验证；LR-002 的 redirectUrl 页面跳转与 LR-035 的游客购物车商品合并仍需补充 UI/端到端验证；LR-029 需 Google OAuth 授权部署；LR-019 与 LR-022 需补齐环境或故障注入能力后复测。

### 11.3 缺陷与风险摘要

风险背景来自 `OWASP_Juice_Shop_风险分析报告.md`：全应用 138 条需求中 High 39 条；“用户登录与会话”模块平均风险分 **17.7**，是高风险域之一。Top 20 中包含 AUTH-004（SQL injection via login email，25）、AUTH-001（Successful login and session establishment，20）、AUTH-003（Server-side login rejection，20）、AUTH-005（Login input handling and error display，20）等认证相关条目。

| 编号 | 关联 LR | 类型 | 描述 | 严重度 |
| --- | --- | --- | --- | --- |
| DEF-001 | LR-014 | 安全缺陷 | `admin@juice-sh.op'--` 可 200 登录并签发 JWT（SQL 注入恒真绕过） | **Critical**（故意漏洞） |
| RISK-001 | LR-018 | 安全风险 | 登录接口 12 次连续错误请求无 429/锁定 | **High** |
| RISK-002 | LR-026 | 安全风险 | 默认 admin/admin123 可登录，弱口令挑战可完成 | **High**（故意挑战） |
| RISK-003 | LR-036 | 安全风险 | testing@ 凭据硬编码于前端，可 admin 登录 | **Medium**（故意挑战） |

**已通过的安全项**：LR-010/015/016/017 XSS 与部分 SQLi 未造成额外泄露；LR-013 软删除用户正确 401；LR-032 无效 TOTP 正确 401。

### 11.4 跳过与阻塞原因（摘要）

| 用例 | pytest | 原因 | 后续建议 |
| --- | --- | --- | --- |
| TC-SEC-014 / LR-014 | **XFail** | SQL 注入 payload 仍返回 200+JWT（靶场故意漏洞 DEF-001） | 真实产品应修复；Juice Shop 上为预期观察 |
| TC-OAUTH-029 / LR-029 | **Skip** | localhost 登录页未渲染 Google OAuth 按钮 | 在 authorizedRedirects 包含当前 origin 的环境重跑 |
| TC-REL-019 / LR-019 | **Skip** | reset-password 连续请求均 500，无法验证 429 阈值 | 配置邮件服务或 staging |
| TC-ERR-022 / LR-022 | **Skip** | 需 DB 故障注入，本次自动化未实施 | docker pause DB 或 mock 500 |

### 11.5 Skip 与 XFail 详细说明

> 完整过程索引（含 pytest 术语、对照总表和结果说明）见 **`docs/测试过程与结果索引.md` §2.1**。以下为摘要。

#### pytest 结果含义

- **Skip**：测试未完整执行，原因通常是环境、第三方配置或故障注入条件不具备；该状态不直接代表被测功能失败。
- **XFail**：测试已执行，结果与安全/质量期望不符，但该现象在当前靶场应用中属于已知预期；pytest 不将其计入 Failed。

#### XFail：TC-SEC-014 / LR-014（SQL 注入登录绕过）

我们在登录邮箱字段输入 `admin@juice-sh.op'--`（SQL 注释符），任意密码。**正常产品**应返回 401、不签发 JWT。**Juice Shop 实际**返回 200 并给出登录 token——因为登录 SQL 未参数化，这是官方 **SQL Injection 挑战**（DEF-001）。脚本检测到 200+JWT 后调用 `pytest.xfail`，表示「安全验收不通过，但在靶场上是已知现象」。证据：`scripts/target_app_tests/test_login_api.py` 131–136 行。

**用例来源（工具 vs 人工）**：LR-014 **需求**在 `login_requirements.csv` **人工编写**；**EP/DT/ST 三条用例主体**由 IntelliTest 综合流程**自动生成**（见 `未优化/LR-014_*.csv`）；**人工优化**阶段改写 oracle 为「安全期望 401 + 若 200 记缺陷」、补全 `admin@juice-sh.op'--` 等种子 payload，并**补漏** `SUP-LR-014-EP-003`（`' OR 1=1--`）；文档代表用例 **TC-SEC-014** 为归纳映射；**PyTest + xfail** 为人工编写的执行脚本。因此，该用例属于工具生成结果经人工审查和自动化实现后的执行项，而不是未审查的原始导出项。

#### Skip：TC-OAUTH-029 / LR-029（Google 登录跳转）

用例要求点击「Google 登录」并跳转到 `accounts.google.com`。**本地 http://localhost:3001 登录页根本没有 Google 按钮**（OAuth 在该 origin 未授权，前端隐藏）。无法点击，故 Skip。**注意**：同环境下的 LR-030（OAuth 应隐藏）已 **Pass**，与「按钮不可见」一致；LR-029 缺的是「已授权、按钮可见」的另一套环境。

#### Skip：TC-REL-019 / LR-019（忘记密码限速）

用例要验证：忘记密码接口在短时间大量请求后返回 **429**。脚本连续调用 `POST /rest/user/reset-password` 时，**全部得到 HTTP 500**（本地常无邮件服务或被安全策略拦截），从未出现 429，无法判断限速逻辑，故 Skip。背景：LR-018 已证实**登录接口无限速**（RISK-001）；LR-019 本用于对照「至少 reset-password 有限速」——对照的后半段在本地未完成。

#### Skip：TC-ERR-022 / LR-022（后端 500 时前端处理）

用例要求：登录时若**数据库故障**导致后端 500，前端应清 token、显示错误。**实现需要在测试中主动弄挂 DB**，本次 Docker 共享环境未做故障注入，脚本直接 Skip。属于测试方法 Blocked，不是「登录 happy path 失败」。

#### 对照总表

| 用例 | pytest | 一句话 | 等于功能坏了？ |
| --- | --- | --- | --- |
| TC-SEC-014 | XFail | SQLi 能登录；靶场故意漏洞 | 真实产品：是；靶场：预期 |
| TC-OAUTH-029 | Skip | 本地无 Google 按钮 | 否 |
| TC-REL-019 | Skip | reset-password 全 500，测不了 429 | 否 |
| TC-ERR-022 | Skip | 未做 DB 故障注入 | 否（未测） |

### 11.6 IntelliTest 工具有效性评价

1. **LLM 黑盒**较旧规则引擎显著减少无效数值 BVA（本次原始导出 138 条，未再批量产生历史 360+ 条噪声），但仍需人工补全 Juice Shop 种子账号和执行数据。
2. **综合流程 ST** 为每条需求提供状态迁移 oracle，与 EP/BVA/DT 形成互补；终稿保留 146 条而非压缩为 36 条，覆盖更细。
3. **安全预言**必须人工改写：工具常写「可能 200 绕过」，执行标准需区分「漏洞观察」与「质量验收」。
4. **PyTest + Playwright 映射**：从 `人工优化/` 生成 `test_cases.json`；API 与 UI 脚本覆盖 36 条代表用例并记录 3 条环境/方法 Skip，**工具链从设计到执行闭环可用**。

### 11.7 结论

登录模块在 localhost:3001 上 **API + UI 自动化回归无意外 Fail**。正确登录、异常登录、客户端校验、Remember Me、2FA、会话/JWT、挑战账号与主要安全探测均得到自动化验证；已知安全问题（SQLi、弱口令、无登录限速、testing 凭据暴露）均被捕获并记录。仍受环境或方法限制的项为 Google OAuth 正向跳转（LR-029）、reset-password 429 限速阈值（LR-019）和 DB 故障注入下的 500 处理（LR-022）。完整用例集见 `人工优化/`；脚本见 `scripts/target_app_tests/`。

## 12. 附录：原始 CSV 需求字段

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

## 13. 附录：当前项目制品清单

| 项目制品 | 当前数量/状态 | 作用 |
| --- | ---: | --- |
| `login_requirements.csv` | 36 条 LR | 登录模块详细需求基线 |
| `未优化/LR-*.csv` | 36 文件，138 条 | IntelliTest 综合流程原始导出 |
| `优化/LR-*.csv` | 36 文件，135 条 | 脚本优化中间稿，仅作过程参考 |
| `人工优化/LR-*.csv` | 36 文件，146 条 | 最终详细测试设计集 |
| `scripts/target_app_tests/test_cases.json` | 146 条 | 由 `build_test_cases.py` 从 `人工优化/` 生成，供自动化追溯 |
| `scripts/target_app_tests/test_login_api.py` | 30 个 API 测试项 | 登录 API、2FA、安全探测、会话、挑战账号、traceability |
| `scripts/target_app_tests/test_login_ui.py` | 9 个 UI 测试项 | 客户端校验、Remember Me、密码显示、Enter、OAuth 可见性 |
| `fixtures/juice-shop/risk_register.csv` | 138 条风险登记 | 全应用风险分析结构化输出 |
| `fixtures/juice-shop/OWASP_Juice_Shop_风险分析报告.md` | 已完成 | 风险背景与测试优先级依据 |

---

