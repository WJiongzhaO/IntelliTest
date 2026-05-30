# OWASP Juice Shop 目标应用风险分析报告

| 项目 | 内容 |
| --- | --- |
| **被测系统** | OWASP Juice Shop（target-apps/juice-shop） |
| **分析对象** | 目标应用功能/安全需求是否未满足时的业务与安全后果 |
| **需求基线** | `fixtures/juice-shop/juice_shop_requirements.csv`（138 条） |
| **分析方法** | AutoTestDesign FR 2.0：Impact（1–5）× Likelihood（1–5）→ 风险分（1–25） |
| **测试优先级** | 风险分 ≥15 → High；8–14 → Medium；≤7 → Low |

---

## 1. 分析目的与方法

### 1.1 什么是这里的「风险」

对每条**软件需求**，评估：若在 OWASP Juice Shop 中该需求**未被满足**（功能错误、安全控制缺失或行为与规格不符），
对用户数据、业务与合规造成的**影响（Impact）**，以及该缺陷**逃逸至生产的可能性（Likelihood）**.

**是** ISTQB / ISO 31000 意义上的需求级风险，用于驱动测试优先级。

### 1.2 评分规则

| 维度 | 1 | 3 | 5 |
| --- | --- | --- | --- |
| **Impact** | 可忽略 | 明显功能/体验影响 | 账户/资金/数据/合规重大损害 |
| **Likelihood** | 极难逃逸 | 一般复杂度 | Juice Shop 已知弱点或高复杂度易漏测 |

**风险分** = Impact × Likelihood（1–25）  
**测试优先级**：High ≥15；Medium 8–14；Low ≤7

需求结构化字段（Input_Fields、Conditions、Expected_Actions）纳入 Likelihood 判断依据。

### 1.3 两类风险来源（本报告结构）

| 部分 | 内容 |
| --- | --- |
| **§3 需求风险登记册** | 138 条 CSV 需求逐条 Impact/Likelihood/风险分 |
| **§4 横切与隐含风险** | CSV 未单独成条但影响整应用的广义问题（如登录无 maxLength、MD5、限流不对称） |

本报告合并呈现**逐条需求风险（§3）**与**应用级弱点及规格缺口（§4）**。

---

## 2. 执行摘要

- 共分析 **138** 条主题级需求，覆盖 **18** 个功能模块。
- 测试优先级分布：**High 39** 条、**Medium 94** 条、**Low 5** 条。
- **最高风险域**：用户登录与会话、SQL/NoSQL 注入相关条目、订单/支付/Deluxe 业务逻辑、文件上传、B2B RCE、资料 SSRF/SSTI。
- **建议测试顺序**：High 安全专项（注入、IDOR、RCE）→ 认证与会话 → 订单/支付/Deluxe 业务逻辑 → 其余 Medium。

### 2.1 模块平均风险分

| 模块 | 平均风险分 | 条数 |
| --- | --- | --- |
| B2B 企业订单 | 18.8 | 5 |
| 用户登录与会话 | 17.7 | 10 |
| 用户资料 | 16.0 | 6 |
| 商品评价 | 14.5 | 8 |
| REST API 与访问控制 | 14.3 | 10 |
| 订单与结账 | 14.2 | 12 |
| 支付与钱包 | 14.1 | 8 |
| 文件上传与静态资源 | 13.5 | 8 |
| Deluxe 会员 | 13.4 | 5 |
| 数据导出与擦除 | 13.4 | 7 |
| 购物车 | 13.2 | 9 |
| 收货地址 | 12.7 | 6 |
| 密码与安全问答 | 12.2 | 8 |
| 双因素认证 | 12.0 | 6 |
| 商品目录与搜索 | 12.0 | 9 |
| 用户注册 | 10.2 | 9 |
| 客户端表现与国际化 | 9.5 | 6 |
| 客户反馈 | 9.0 | 6 |

### 2.2 Top 20 高风险需求

| 排名 | ID | 模块 | 标题 | 风险分 | 测试优先级 |
| --- | --- | --- | --- | --- | --- |
| 1 | ADR-005 | 收货地址 | IDOR on address by id | 25 | High |
| 2 | API-002 | REST API 与访问控制 | Admin role enforcement | 25 | High |
| 3 | AUTH-004 | 用户登录与会话 | SQL injection via login email | 25 | High |
| 4 | B2B-003 | B2B 企业订单 | B2B RCE via order payload | 25 | High |
| 5 | B2B-004 | B2B 企业订单 | B2B endpoint authentication | 25 | High |
| 6 | CART-002 | 购物车 | IDOR read foreign basket | 25 | High |
| 7 | CAT-004 | 商品目录与搜索 | Search SQL injection in q parameter | 25 | High |
| 8 | DAT-005 | 数据导出与擦除 | Data erasure LFR vulnerability | 25 | High |
| 9 | DLX-004 | Deluxe 会员 | Free deluxe membership abuse | 25 | High |
| 10 | FILE-003 | 文件上传与静态资源 | XML upload XXE surface | 25 | High |
| 11 | ORD-007 | 订单与结账 | Track order NoSQL injection | 25 | High |
| 12 | PAY-004 | 支付与钱包 | IDOR on payment cards | 25 | High |
| 13 | PRF-004 | 用户资料 | Profile image URL upload SSRF surface | 25 | High |
| 14 | PRF-005 | 用户资料 | Profile SSTI in username display | 25 | High |
| 15 | REV-004 | 商品评价 | Update reviews batch NoSQL | 25 | High |
| 16 | API-001 | REST API 与访问控制 | JWT required on protected routes | 20 | High |
| 17 | API-008 | REST API 与访问控制 | JWT tampering rejected | 20 | High |
| 18 | AUTH-001 | 用户登录与会话 | Successful login and session establishment | 20 | High |
| 19 | AUTH-003 | 用户登录与会话 | Server-side login rejection | 20 | High |
| 20 | AUTH-005 | 用户登录与会话 | Login input handling and error display | 20 | High |

---

## 3. 需求风险登记册（138 条）

完整字段见 `fixtures/juice-shop/risk_register.csv`（与 IntelliTest 风险分析导出列一致，可导入 Excel）。

列：`ID`, `title`, `impact`, `likelihood`, `risk_score`, `priority`, `impact_rationale`, `likelihood_rationale`。

| ID | 需求标题 | I | L | 分 | 优先级 | 影响说明 | 可能性说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AUTH-001 | Successful login and session establishment | 4 | 5 | 20 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| AUTH-002 | Login form client-side validation | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| AUTH-003 | Server-side login rejection | 4 | 5 | 20 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| AUTH-004 | SQL injection via login email | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| AUTH-005 | Login input handling and error display | 4 | 5 | 20 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| AUTH-006 | JWT and session lifecycle | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| AUTH-007 | No rate limiting on login endpoint | 4 | 5 | 20 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| AUTH-008 | Remember-me OAuth and login UX | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| AUTH-009 | 2FA gate after password at login | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| AUTH-010 | Login error handling and exposed credentials | 4 | 5 | 20 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| REG-001 | Valid user registration | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| REG-002 | Duplicate email rejected | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| REG-003 | Password mismatch blocks registration | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| REG-004 | Security question required | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| REG-005 | Email sanitization on registration | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| REG-006 | Empty required fields rejected | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| REG-007 | Registration creates wallet | 4 | 2 | 8 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 逻辑简单或已有明确校验，逃逸概率较低 |
| REG-008 | Weak or short password on registration | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| REG-009 | Invalid security answer rejected | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| PWD-001 | Password reset with valid email | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PWD-002 | Password reset rate limited | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PWD-003 | Password reset unknown email | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| PWD-004 | Change password with current credentials | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PWD-005 | Change password without current password | 5 | 4 | 20 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | 涉及多组件/边界条件，历史同类缺陷常见 |
| PWD-006 | Retrieve security question for reset | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| PWD-007 | Security answer verification on reset | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PWD-008 | Login vs reset rate limit contrast | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| TFA-001 | 2FA verify with valid TOTP after tmpToken | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| TFA-002 | 2FA verify with invalid TOTP | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| TFA-003 | 2FA setup returns secret and QR | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| TFA-004 | 2FA status reflects enrollment | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| TFA-005 | 2FA disable requires valid TOTP | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| TFA-006 | 2FA verify rejects expired tmpToken | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PRF-001 | View user profile page | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| PRF-002 | Update profile username | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PRF-003 | Profile image file upload | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| PRF-004 | Profile image URL upload SSRF surface | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| PRF-005 | Profile SSTI in username display | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| PRF-006 | Profile update CSRF token | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| ADR-001 | List user addresses | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| ADR-002 | Create delivery address | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| ADR-003 | Update own address | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| ADR-004 | Delete own address | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| ADR-005 | IDOR on address by id | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| ADR-006 | Create address missing required fields | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| CAT-001 | List products via API | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| CAT-002 | Product detail by id | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| CAT-003 | Search products by keyword | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| CAT-004 | Search SQL injection in q parameter | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| CAT-005 | Admin product API authorization | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| CAT-006 | Soft-deleted products in basket context | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| CAT-007 | Empty search query | 2 | 2 | 4 | Low | 影响有限，主要为展示或辅助功能 | 逻辑简单或已有明确校验，逃逸概率较低 |
| CAT-008 | Product price displayed in deluxe context | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| CAT-009 | Delete product admin only | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| CART-001 | Retrieve own basket | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| CART-002 | IDOR read foreign basket | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| CART-003 | Add item to basket | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| CART-004 | Update basket item quantity | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| CART-005 | Remove item from basket | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| CART-006 | Quantity zero or negative rejected | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| CART-007 | Guest basket merge on login | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| CART-008 | Checkout entry from basket | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| CART-009 | Add out-of-stock product | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| ORD-001 | Place order from basket checkout | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| ORD-002 | Apply coupon to basket | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| ORD-003 | Invalid coupon rejected | 3 | 4 | 12 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 涉及多组件/边界条件，历史同类缺陷常见 |
| ORD-004 | Order history for logged-in user | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| ORD-005 | All orders admin/accounting view | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| ORD-006 | Track order by id | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| ORD-007 | Track order NoSQL injection | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| ORD-008 | Delivery options list | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| ORD-009 | Toggle delivery status accounting | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| ORD-010 | Checkout decrements inventory | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| ORD-011 | Checkout wallet deduction | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| ORD-012 | Checkout empty basket rejected | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PAY-001 | List saved payment cards | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PAY-002 | Add payment card | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PAY-003 | Delete own payment card | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PAY-004 | IDOR on payment cards | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| PAY-005 | Get wallet balance | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PAY-006 | Top up wallet balance | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| PAY-007 | Card number validation boundary | 3 | 4 | 12 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 涉及多组件/边界条件，历史同类缺陷常见 |
| PAY-008 | Expired payment card rejected | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| B2B-001 | Submit B2B order with orderLines | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| B2B-002 | B2B order schema validation | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| B2B-003 | B2B RCE via order payload | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| B2B-004 | B2B endpoint authentication | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| B2B-005 | B2B empty orderLines rejected | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| REV-001 | List reviews for product | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| REV-002 | Create product review | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| REV-003 | Forged review author | 4 | 5 | 20 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| REV-004 | Update reviews batch NoSQL | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| REV-005 | Like product review | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| REV-006 | Review list NoSQL DoS | 4 | 5 | 20 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| REV-007 | Stored XSS in review message | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| REV-008 | Unauthenticated review creation blocked | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| FDB-001 | Submit feedback with captcha | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| FDB-002 | Feedback captcha bypass | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| FDB-003 | List feedback entries | 2 | 2 | 4 | Low | 影响有限，主要为展示或辅助功能 | 逻辑简单或已有明确校验，逃逸概率较低 |
| FDB-004 | Forged feedback userId | 4 | 5 | 20 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| FDB-005 | Get captcha image or text | 2 | 2 | 4 | Low | 影响有限，主要为展示或辅助功能 | 逻辑简单或已有明确校验，逃逸概率较低 |
| FDB-006 | Empty feedback comment rejected | 2 | 4 | 8 | Medium | 影响有限，主要为展示或辅助功能 | 涉及多组件/边界条件，历史同类缺陷常见 |
| DLX-001 | Query deluxe membership status | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| DLX-002 | Upgrade to deluxe via wallet | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| DLX-003 | Upgrade to deluxe via card | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| DLX-004 | Free deluxe membership abuse | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| DLX-005 | Deluxe member sees deluxe pricing | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| DAT-001 | Request personal data export | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| DAT-002 | Data export image captcha required | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| DAT-003 | Data export cross-store aggregation | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| DAT-004 | Request data erasure | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| DAT-005 | Data erasure LFR vulnerability | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| DAT-006 | Privacy request API | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| DAT-007 | Data erasure unauthenticated blocked | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| FILE-001 | Generic file upload | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| FILE-002 | ZIP upload and extraction | 5 | 4 | 20 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | 涉及多组件/边界条件，历史同类缺陷常见 |
| FILE-003 | XML upload XXE surface | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| FILE-004 | Memory photo upload and list | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| FILE-005 | FTP static directory listing | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| FILE-006 | Quarantine folder access | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| FILE-007 | Upload size limit boundary | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| FILE-008 | Disallowed file type rejected | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| API-001 | JWT required on protected routes | 5 | 4 | 20 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | 涉及多组件/边界条件，历史同类缺陷常见 |
| API-002 | Admin role enforcement | 5 | 5 | 25 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | Juice Shop 故意保留该弱点或实现简单，未经专项测试极易暴露 |
| API-003 | Deluxe role pricing access | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| API-004 | Authenticated users debug endpoint | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| API-005 | denyAll middleware blocks routes | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| API-006 | CORS policy behavior | 3 | 4 | 12 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 涉及多组件/边界条件，历史同类缺陷常见 |
| API-007 | API rate limiting on sensitive routes | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| API-008 | JWT tampering rejected | 5 | 4 | 20 | High | 可导致账户接管、数据泄露、远程代码执行或资金/隐私重大损失 | 涉及多组件/边界条件，历史同类缺陷常见 |
| API-009 | Finale REST CRUD authorization matrix | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| API-010 | Accounting role order access | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| UI-001 | Registration and checkout form validation | 4 | 4 | 16 | High | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 涉及多组件/边界条件，历史同类缺陷常见 |
| UI-002 | JWT stored in localStorage and cookie | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| UI-003 | Language selection i18n | 2 | 2 | 4 | Low | 影响有限，主要为展示或辅助功能 | 逻辑简单或已有明确校验，逃逸概率较低 |
| UI-004 | Route guard for authenticated pages | 4 | 3 | 12 | Medium | 影响核心交易、认证或敏感个人数据，业务中断或合规风险明显 | 有一定实现复杂度，常规测试可能遗漏 |
| UI-005 | Google OAuth button visibility | 3 | 3 | 9 | Medium | 功能错误或局部数据不一致，影响用户体验或局部安全 | 有一定实现复杂度，常规测试可能遗漏 |
| UI-006 | Basket count in navbar | 2 | 2 | 4 | Low | 影响有限，主要为展示或辅助功能 | 逻辑简单或已有明确校验，逃逸概率较低 |

---

## 4. 横切与隐含风险（未单独列入 CSV 的广义风险）

以下问题在 Juice Shop **源码中可验证**或**规格未定义**，但未在 138 条中各占一行；
部分已由 §3 多条需求间接覆盖，测试规划时宜一并纳入。

| ID | 类别 | 描述 | I | L | 分 | 优先级 | 说明 | 关联需求 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BR-001 | 输入规格缺口 | 登录/部分 API 未定义 email、password 最大长度与字符集上限 | 3 | 3 | 9 | Medium | 无 maxLength 时超长输入可能导致 DoS、日志膨胀或 DB 截断，属健壮性/可用性风险而非已写明的功能需求 | AUTH-002、AUTH-005；138 条 CSV 未单独列项 |
| BR-002 | 密码策略 | 全站使用 MD5 存储密码、登录 minLength(1)，弱口令可注册/登录 | 5 | 5 | 25 | High | 加密失败类风险；与 AUTH-001/REG-008 相关但 CSV 未逐条展开弱口令字典 | AUTH-001、REG-008、PWD-* |
| BR-003 | 认证不一致 | 注册路径 sanitize email，登录路径 SQL 拼接，同源输入处理不一致 | 4 | 4 | 16 | High | 攻击面不对称；REG-005 vs AUTH-004 | REG-005、AUTH-004 |
| BR-004 | 限流策略缺口 | 登录无 rate limit，重置密码有限流，暴力破解面不对称 | 4 | 5 | 20 | High | AUTH-007、PWD-008 已覆盖；属横切认证风险 | AUTH-007、API-007 |
| BR-005 | 会话与令牌 | JWT 存 localStorage、多会话并存、cookie 与 JWT 过期不一致 | 4 | 4 | 16 | High | XSS 窃取令牌与会话 fixation 类广义风险 | AUTH-006、UI-002 |
| BR-006 | 越权横切 | Basket/Address/Card 等资源 ID 可被猜测或遍历（IDOR 面） | 5 | 4 | 20 | High | 多模块重复模式；CART-002、ADR-005、PAY-004 等已列但需横切测试 | CART、ADR、PAY 模块 |
| BR-007 | 依赖与配置 | npm 依赖 CVE、默认种子用户、调试/静态目录暴露 | 4 | 3 | 12 | Medium | A05/A06 类；FILE-005、AUTH-010 部分覆盖 | FILE、API、AUTH-010 |
| BR-008 | 业务逻辑 | 价格/优惠券/钱包/Deluxe 组合结账可被篡改（负价、免费会员） | 5 | 4 | 20 | High | A04 不安全设计；ORD、DLX、PAY 多条需求相关 | ORD-002、DLX-004、PAY-006 |
| BR-009 | CORS 策略 | server.ts 对全部路由启用 cors()，注释写明「Allow everything」 | 4 | 4 | 16 | High | 跨站请求可携带用户 Cookie/JWT 调用 REST；与 API-006 相关但属全局配置风险 | API-006 |
| BR-010 | HTTP 安全头 | helmet.xssFilter 被注释禁用，REST 持久化 XSS 无浏览器级反射过滤 | 4 | 4 | 16 | High | 评价/用户名等字段可存脚本；与 REV-007、PRF-005 叠加 | REV-007、PRF-005、UI-002 |
| BR-011 | API 文档暴露 | /api-docs 挂载 swagger.yml，B2B v2 等接口 schema 无认证可读 | 3 | 5 | 15 | High | 攻击面枚举成本低；B2B-003/004 利用路径可被快速定位 | B2B-003、B2B-004、API-009 |
| BR-012 | 静态目录泄露 | /ftp、/encryptionkeys、/support/logs 等目录可浏览或下载敏感文件 | 4 | 4 | 16 | High | robots.txt 仅 Disallow /ftp，其余路径仍可达；日志含访问记录 | FILE-005、FILE-006、AUTH-010 |
| BR-013 | 路由归一化 | 中间件将 req.url 中连续斜杠折叠为单斜杠，可能绕过部分路径匹配 | 4 | 3 | 12 | Medium | 历史上有利用双斜杠绕过 ACL 的同类缺陷；需与 API 授权矩阵联测 | API-002、API-005 |
| BR-014 | Cookie 签名 | cookieParser 使用硬编码密钥「kekse」，language 等 Cookie 可被伪造 | 3 | 3 | 9 | Medium | i18n cookie 篡改影响有限，但反映密钥管理薄弱 | UI-003 |
| BR-015 | 双存储架构 | Sequelize/SQLite 存用户订单，MongoDB 存评价等；导出/擦除需跨库一致 | 4 | 4 | 16 | High | DAT-003/005 已列条目；单库测试无法覆盖残留数据 | DAT-003、DAT-005、REV-004、ORD-007 |
| BR-016 | Finale REST | finale 为 15+ 模型自动生成 /api/* CRUD，与手工 security 中间件矩阵不完全一致 | 5 | 4 | 20 | High | Products PUT 等路由曾故意注释 isAuthorized；批量 CRUD 授权易漏 | API-009、CAT-005 |
| BR-017 | NoSQL 面 | /rest/products/reviews、track-order 等 Mongo 端点与 SQL REST 混布，注入面分散 | 5 | 5 | 25 | High | ORD-007、REV-004/006 已列；测试需区分存储后端 | ORD-007、REV-004、REV-006 |
| BR-018 | Web3 与 Chat | /rest/web3/*、/rest/chat 等扩展端点无统一 JWT 门槛，含合约 exploit 监听 | 4 | 3 | 12 | Medium | 138 条 CSV 未逐端点展开；属新增攻击面 | API-001（横切） |
| BR-019 | 运维与调试面 | continue-code、/rest/admin/*、/snippets/* 等暴露版本、配置与漏洞代码片段 | 3 | 4 | 12 | Medium | 信息泄露辅助后续攻击；API-004 部分覆盖 | API-004、AUTH-010 |

### 4.1 关于「邮箱长度、密码上限」等边界

登录界面 Angular 表单仅 `required` + 密码 `minLength(1)`，**未定义** email/password 的 `maxLength`。
因此 138 条 CSV **未**将「邮箱 256 字符边界」列为独立需求——这不是遗漏测试范围，而是**应用未规定该规格**（见 BR-001）。
若进行探索性测试发现 DoS 或截断，应记录为**健壮性发现**，并引用 BR-001，而非虚构对应 FR 条目。

---

## 5. 测试优先级建议

| 优先级 | 建议动作 | 代表模块/需求 |
| --- | --- | --- |
| **P0（立即）** | 安全专项 + 认证域 | AUTH-004/007、CAT-004、ORD-007、B2B-003、PRF-004/005、DLX-004、FILE-002/003、PWD-005 |
| **P1（计划内）** | 全应用功能回归 + IDOR 矩阵 | CART、ADR、PAY、ORD、API |
| **P2（时间允许）** | UI/i18n、低影响边界 | UI、FDB、CAT-007 |
