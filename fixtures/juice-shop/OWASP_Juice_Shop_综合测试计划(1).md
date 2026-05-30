# OWASP Juice Shop 综合测试计划
## —— 基于 AutoTestDesign AI 驱动自动化测试设计工具

| 项目 | 内容 |
| --- | --- |
| **被测系统** | OWASP Juice Shop v17.x（完整电商应用） |
| **测试设计工具** | AutoTestDesign（自研 AI 驱动自动化测试设计平台） |
| **测试类型** | 功能测试 + 安全测试 + 性能测试 + 兼容性测试 |
| **测试范围** | 全部核心业务模块（登录、注册、商品、购物车、支付、搜索、管理后台等） |
| **用例总数** | 200+ 条（由 AutoTestDesign 自动生成） |
| **优先级分布** | Critical: 30, High: 50, Medium: 80, Low: 40 |
| **预计工时** | 15-20 小时（AI 辅助，较纯手工缩短 60%+） |
| **测试团队** | 王炯昭、李昊天、李宇轩、刘逸飞、宋文轩 |

### 文档修订历史

| 版本 | 日期 | 修订人 | 修订内容 |
| --- | --- | --- | --- |
| v1.0 | 2026-05-29 | 测试团队 | 初始版本，基于 AutoTestDesign 工具重塑测试计划 |

---

## 1. 项目背景与测试范围 (Project Scope & Test Items)

### 1.1 项目背景与目标

#### 1.1.1 测试活动定位
本次测试活动的核心目标是**验证自研【AutoTestDesign】AI 驱动自动化测试设计工具在复杂 Web 应用上的有效性和覆盖率**。OWASP Juice Shop 作为业界知名的故意包含安全漏洞的电商应用，具有完整的业务逻辑链、丰富的安全风险场景和复杂的交互流程，是检验 AutoTestDesign 工具能力的理想目标系统。

#### 1.1.2 AutoTestDesign 工具核心价值
AutoTestDesign 是一款符合 ISTQB 标准与 ISO/IEC/IEEE 29119 规范的 AI 辅助测试工程（AISTE）平台，其核心能力包括：
- **需求结构化解析**：自动识别自然语言需求中的覆盖项（Coverage Items, CI）
- **风险智能分析**：基于历史数据和规则引擎进行多维度风险评估
- **测试技术自动选型**：根据需求特征自动选择 EP/BVA/DT/状态迁移等测试技术
- **用例自动生成**：结合 LLM 推理生成结构化测试用例（JSON/CSV 格式）
- **人机交互审查**：提供可视化界面供测试人员审查、修订和补充 AI 生成的用例

#### 1.1.3 测试目标
- **主要目标**：通过系统化测试 OWASP Juice Shop，验证 AutoTestDesign 工具在黑盒测试设计（等价类划分、边界值分析、决策表）、白盒建模（状态转换图）、安全测试（OWASP Top 10 覆盖）等方面的生成质量与覆盖率
- **次要目标**： 
  - 全面验证 OWASP Juice Shop 各功能模块的业务逻辑正确性
  - 系统性识别并记录所有安全漏洞（OWASP Top 10 + 其他常见漏洞）
  - 评估应用的可用性、性能和兼容性
  - 为安全培训和渗透测试提供完整的测试基线

### 1.2 目标应用架构描述

OWASP Juice Shop 采用典型的前后端分离架构，技术栈如下：

```
┌─────────────────────────────────────┐
│       Client Layer (Frontend)       │
├─────────────────────────────────────┤
│  • Framework: Angular 17.x          │
│  • Language: TypeScript             │
│  • UI Library: Angular Material     │
│  • State Management: RxJS           │
│  • Build Tool: Webpack              │
└─────────────────────────────────────┘
         ↓ REST API / WebSocket
┌─────────────────────────────────────┐
│       Server Layer (Backend)        │
├─────────────────────────────────────┤
│  • Runtime: Node.js 18.x/20.x LTS   │
│  • Framework: Express.js            │
│  • Authentication: JWT (RS256)   │
│  • Security: Helmet, CORS, rate-limit |
│  • Validation: Joi / express-validator |
└─────────────────────────────────────┘
         ↓ ORM / Query Builder
┌─────────────────────────────────────┐
│       Data Layer (Database)         │
├─────────────────────────────────────┤
│  • Database: SQLite (default)       │
│  • ORM: Sequelize                   │
│  • Seed Data: Pre-loaded test users |
│  • Port: 3000                       │
└─────────────────────────────────────┘
```

**关键架构特性对测试的影响**：
- **Angular 前端**：需关注组件生命周期、双向数据绑定、路由守卫等 Angular 特有机制引发的缺陷
- **Express 中间件链**：认证、授权、日志、错误处理等中间件的执行顺序可能引发安全绕过
- **SQLite 数据库**：默认配置下可能存在 SQL 注入风险，且缺乏生产级数据库的并发控制
- **JWT 认证**：需重点测试令牌伪造、过期处理、刷新机制等安全场景

### 1.3 测试范围

#### 纳入测试的模块

| 模块名称 | 功能描述 | AutoTestDesign 覆盖策略 | 优先级 |
| --- | --- | --- | --- |
| **用户登录与会话** | 登录、OAuth 跳转、JWT 与会话管理、whoami | EP + BVA + DT + 状态迁移 + 安全场景 | Critical |
| **用户注册** | 新用户注册、安全问题绑定、重复邮箱校验 | EP + DT | Critical |
| **密码与安全问答** | 密码重置与修改、安全问题、重置限流 | EP + BVA + DT | Critical |
| **双因素认证** | TOTP 绑定、验证、禁用与状态查询 | DT + ST | Critical |
| **用户资料** | 个人资料查询与修改、头像上传（含 URL 抓取） | EP + SSRF/SSTI 专项 | High |
| **收货地址** | 收货地址增删改查与越权隔离 | EP + IDOR | High |
| **商品 catalog 与搜索** | 商品列表与详情、关键词搜索及注入面 | EP + 安全输入测试 | High |
| **购物车** | 购物车查询与越权、商品增删改、数量边界、游客篮合并 | 状态迁移 + EP + 业务逻辑 | High |
| **订单与结账** | 下单、订单历史、物流跟踪、优惠券、库存扣减 | DT + 状态转换 + 权限 | Critical |
| **支付与钱包** | 银行卡管理、钱包余额与充值 | EP + BVA + IDOR | Critical |
| **B2B 企业订单** | 企业 orderLines 接口与沙箱执行面 | DT + 安全场景 | Critical |
| **商品评价** | 商品评价、评分与点赞、NoSQL 与伪造 author | EP + NoSQL/XSS | Medium |
| **客户反馈** | 客户反馈提交、算术验证码 | EP + DT | Medium |
| **Deluxe 会员** | Deluxe 会员状态查询与升级支付 | DT + EP | Medium |
| **数据导出与擦除** | 个人数据导出、擦除请求与隐私 API | DT + 图像验证码 | Medium |
| **文件上传与静态资源** | 通用文件上传、压缩包与结构化文件、记忆照片、静态目录 | BVA + 路径/类型安全 | High |
| **REST API 与访问控制** | 接口鉴权、多角色权限、访问频率限制、跨域策略 | 权限矩阵 + EP + 限流 | Critical |
| **客户端表现与国际化** | 前端表单校验、浏览器存储、页面路由、多语言 | 客户端逻辑 + 编码/路径 | Medium |

#### 排除范围
- 第三方 OAuth 提供商的实际可用性（仅验证跳转逻辑）
- 真实支付网关集成（使用模拟环境）
- 邮件/SMS 发送服务的实际投递（仅验证触发逻辑）

#### 需求分层说明

本计划中的测试项与 18 个功能模块，以 **`fixtures/juice-shop/juice_shop_requirements.csv`（138 条主题级需求）** 为应用级需求基线，用于风险分析与套件规划。

**登录模块**的详细测试设计与自动化执行，采用项目根目录 **`login_requirements.csv`（36 条 LR）** 作为用例级需求输入；其与全量需求中 AUTH-001～AUTH-010 的对应关系见 `fixtures/juice-shop/REQUIREMENTS_ANALYSIS.md` §3 及 `JuiceShop登录模块详细测试设计与执行文档(1).md` 追溯矩阵。

两套需求服务于不同课程交付物（风险报告/测试计划 vs 单模块详细执行），**不是重复或矛盾的两份范围**。

---

## 2. 高级测试套件设计 (High-level Test Suite Design)

### 2.1 基于风险分析的测试技术选型

AutoTestDesign 工具通过以下工作流自动生成测试套件：

```
┌──────────────────┐
│  需求输入 (FR/NFR)│
└────────┬─────────┘
         ↓
┌──────────────────┐
│  LLM 需求结构化   │ ← AutoTestDesign 自动识别 Coverage Items (CI)
└────────┬─────────┘
         ↓
┌──────────────────┐
│  风险评分引擎     │ ← 基于历史数据 + 规则库计算 Risk Score
└────────┬─────────┘
         ↓
┌──────────────────┐
│  测试技术自动选型 │ ← EP/BVA/DT/状态迁移/安全专项
└────────┬─────────┘
         ↓
┌──────────────────┐
│  测试用例生成     │ ← LLM 推理 + 模板填充 → JSON/CSV
└────────┬─────────┘
         ↓
┌──────────────────┐
│  人机交互审查     │ ← 测试人员修订、补充、确认
└────────┬─────────┘
         ↓
┌──────────────────┐
│  导出执行框架     │ ← Playwright/k6 脚本映射
└──────────────────┘
```

### 2.2 黑盒测试技术覆盖矩阵

| 测试技术 | AutoTestDesign 应用场景 | 覆盖模块 | 生成用例数 |
| --- | --- | --- | --- |
| **等价类划分 (EP)** | 输入验证、表单字段、API 参数合法性检查 | 全部模块 | 60+ |
| **边界值分析 (BVA)** | 数值范围（价格/数量）、字符串长度、分页边界 | 商品、购物车、订单 | 40+ |
| **决策表 (DT)** | 条件组合（登录凭证/权限矩阵）、业务流程分支 | 登录、支付、管理后台 | 50+ |
| **状态迁移测试** | 订单状态流转、用户会话生命周期、购物车状态机 | 订单、会话管理、购物车 | 30+ |
| **错误推测法** | 异常输入、并发操作、网络中断、超时场景 | 全部模块 | 20+ |

**技术选型依据**（由 AutoTestDesign 风险引擎自动判定）：
- **高安全风险模块**（登录、支付、管理后台）：优先采用决策表（DT）覆盖所有条件组合
- **数值敏感模块**（商品价格、库存、订单金额）：强制应用边界值分析（BVA）
- **状态依赖模块**（订单流转、会话管理）：启用状态转换建模生成路径覆盖用例
- **输入密集型模块**（搜索框、评论、个人资料）：使用等价类划分（EP）确保有效/无效输入全覆盖

### 2.3 白盒测试技术覆盖

| 技术 | AutoTestDesign 支持方式 | 工具集成 |
| --- | --- | --- |
| **代码审查辅助** | LLM 分析 Node.js/Express 后端逻辑、Angular 前端组件复杂度 | ESLint、SonarQube 报告导入 |
| **状态建模** | 自动提取用户认证状态、订单流转、购物车状态的 FSM（有限状态机） | IntelliTest StateTransition 引擎 |
| **路径覆盖分析** | 基于 AST 解析 API 路由、中间件链、错误处理分支 | Coverage 工具数据对接 |
| **依赖漏洞扫描** | 调用 npm audit API 分析第三方库 CVE | Snyk/GitHub Dependabot 集成 |

### 2.4 安全测试专项（OWASP Top 10 覆盖）

AutoTestDesign 内置安全测试规则库，自动将 OWASP Top 10 映射为可执行的测试用例：

| 漏洞类型 | AutoTestDesign 生成策略 | 目标模块 | 用例数 |
| --- | --- | --- | --- |
| **A01:2021 - 失效访问控制** | IDOR 探测 + 垂直/水平权限提升矩阵 | 用户资料、订单、管理后台 | 25 |
| **A02:2021 - 加密失败** | 敏感数据明文传输检测 + 弱加密算法识别 | 登录、支付、API | 15 |
| **A03:2021 - 注入** | SQL/NoSQL/OS/LDAP 注入 payload 自动生成 | 登录、搜索、商品查询 | 30 |
| **A04:2021 - 不安全设计** | 业务逻辑缺陷探测（价格篡改、库存绕过） | 购物车、支付、优惠券 | 20 |
| **A05:2021 - 安全配置错误** | 默认凭据扫描 + 调试信息泄露检测 + CORS 校验 | 全部模块 | 15 |
| **A06:2021 - 易受攻击组件** | npm 依赖树 CVE 匹配 + 过时版本告警 | 全部依赖 | 10 |
| **A07:2021 - 认证与标识失败** | 弱口令字典攻击 + 会话固定测试 + JWT 伪造尝试 | 登录、会话管理 | 20 |
| **A08:2021 - 软件与数据完整性失败** | 反序列化 payload 生成 + CI/CD 供应链风险扫描 | 文件上传、API | 10 |
| **A09:2021 - 安全日志与监控失败** | 日志缺失场景枚举 + 告警未触发验证 | 全部模块 | 10 |
| **A10:2021 - SSRF** | 服务器端请求伪造 URL 探测 + 内网地址扫描 | 图片加载、Webhook | 10 |

**其他安全测试扩展**：
- **XSS 测试**：反射型、存储型、DOM-based（XSS polyglot payload 自动生成）
- **CSRF 测试**：关键操作令牌验证（缺少 token/过期 token/重放 token）
- **文件上传漏洞**：恶意文件（.php/.jsp/.exe）、路径遍历（../../etc/passwd）、MIME 类型绕过
- **XXE 测试**：XML 解析漏洞探测（如 API 接受 XML 输入）
- **业务逻辑漏洞**：价格篡改（负数/超大数）、库存绕过（并发下单）、优惠券滥用（重复使用）

### 2.5 性能测试策略

| 测试类型 | AutoTestDesign 生成场景 | 指标要求 | 工具 |
| --- | --- | --- | --- |
| **响应时间** | P95 < 2s，P99 < 5s（商品列表、搜索、下单） | k6 自动生成分布式负载脚本 | k6、Artillery |
| **并发用户** | 支持 100+ 并发（峰值 200） | 阶梯式增压模型 | k6 |
| **吞吐量** | > 50 req/s（核心 API） | RPS 监控 + 错误率告警 | k6 |
| **资源使用** | CPU < 80%，内存 < 2GB | Docker Stats 实时采集 | Docker Stats |

### 2.6 兼容性测试矩阵

| 维度 | AutoTestDesign 覆盖范围 | 验证方式 |
| --- | --- | --- |
| **浏览器** | Chrome 120+、Firefox 115+、Edge 120+、Safari 17+ | Playwright 多浏览器并行执行 |
| **设备** | Desktop (1920x1080)、Tablet (768x1024)、Mobile (375x667) | Viewport 自动切换 + 截图对比 |
| **操作系统** | Windows 11、macOS Sonoma、Ubuntu 22.04 | CI/CD 矩阵构建 |
| **Node.js** | 18.x LTS、20.x LTS | Docker 多版本容器测试 |

---

## 3. 组织架构与职责分工 (Organization Chart)

### 3.1 基于 AutoTestDesign 工具的团队角色定义

与传统测试团队不同，本项目的 5 位成员在**使用 AutoTestDesign 工具进行测试活动中**承担以下特定职责：

| 成员姓名 | 角色名称 | 核心职责 | 关键产出 |
| --- | --- | --- | --- |
| **王炯昭** | **AI 测试负责人**<br>(AI Testing Lead) | 1. 配置 AutoTestDesign 底层系统 Prompt 及交互规则<br>2. 调优 LLM 参数（temperature/top_p）以平衡用例多样性与准确性<br>3. 维护风险评分规则库与安全测试 payload 库<br>4. 协调团队成员的工具使用培训与技术答疑 | - 系统 Prompt 配置文件<br>- LLM 参数调优报告<br>- 风险规则库更新日志 |
| **李昊天** | **需求交互审查员**<br>(Requirement Designer) | 1. 在 AutoTestDesign 界面输入自然语言需求（FR/NFR）<br>2. 审查 AI 自动识别的 Coverage Items (CI)，修订遗漏或错误的覆盖项<br>3. 手动补充 AI 未能识别的边缘场景（如特殊业务逻辑）<br>4. 确认测试技术选型（EP/BVA/DT）的合理性 | - 结构化需求文档（JSON）<br>- CI 审查修订记录<br>- 测试技术选型确认单 |
| **李宇轩** | **自动化脚本转化员**<br>(Automation Script Converter) | 1. 接收 AutoTestDesign 导出的结构化测试用例（JSON/CSV）<br>2. 将用例映射为 Playwright UI 自动化脚本（Python/TypeScript）<br>3. 将性能测试场景转化为 k6 负载脚本（JavaScript）<br>4. 维护脚本模板库，确保生成代码符合团队规范 | - Playwright 测试脚本集<br>- k6 性能测试脚本集<br>- 脚本映射规则文档 |
| **刘逸飞** | **安全测试专家**<br>(Security Testing Specialist) | 1. 审查 AutoTestDesign 生成的安全测试用例（OWASP Top 10 覆盖）<br>2. 手动执行高风险漏洞的 PoC 验证（SQL 注入/XSS/文件上传）<br>3. 使用 Burp Suite/ZAP 进行深度渗透测试，补充 AI 遗漏的场景<br>4. 编写漏洞报告并提供修复建议 | - 安全测试报告<br>- 漏洞 PoC 集合<br>- 修复建议文档 |
| **宋文轩** | **质量度量与报告员**<br>(Quality Metrics Analyst) | 1. 监控 AutoTestDesign 用例生成质量（覆盖率/准确率/重复率）<br>2. 统计测试执行结果（Pass/Fail/Blocked 比率）<br>3. 生成阶段性测试报告与最终验收报告<br>4. 维护缺陷跟踪看板（Jira/GitHub Issues） | - 质量度量仪表盘<br>- 阶段性测试报告<br>- 缺陷统计分析表 |

### 3.2 协作流程图

```
┌─────────────┐
│ 王炯昭      │ ← 配置 AutoTestDesign 系统 Prompt + 风险规则库
└──────┬──────┘
       ↓
┌─────────────┐
│ 李昊天      │ ← 输入需求 → 审查 AI 生成的 CI → 确认测试技术选型
└──────┬──────┘
       ↓
┌─────────────┐
│ AutoTest    │ ← 自动生成测试用例(JSON/CSV)
│ Design      │
└──────┬──────┘
       ↓
┌─────────────┐     ┌─────────────┐
│ 李宇轩      │     │ 刘逸飞      │
│ (功能用例)  │     │ (安全用例)  │
│ → Playwright│     │ → Burp Suite│
│ → k6        │     │ → 手动 PoC  │
└──────┬──────┘     └──────┬──────┘
       ↓                   ↓
┌─────────────────────────────────┐
│     宋文轩                      │
│ 收集执行结果 → 生成质量报告      │
│ 维护缺陷看板 → 输出最终验收报告   │
└─────────────────────────────────┘
```

### 3.3 沟通机制

| 活动 | 频率 | 参与人 | 产出 |
| --- | --- | --- | --- |
| **每日站会** | 每天 9:00 | 全体测试成员 | 昨日进展、今日计划、阻塞问题 |
| **AI 生成质量 Review** | 每周 2 次 | 王炯昭 + 李昊天 | CI 识别准确率、用例重复率分析 |
| **缺陷评审** | 每周 2 次 | 测试 + 开发 | 缺陷优先级确认、分配 |
| **周报复盘** | 每周五 16:00 | 全体项目组 | 周报、风险预警、下周计划 |
| **阶段性 Review** | 每阶段结束 | 全体项目组 | 阶段报告、经验总结 |

---

## 4. 成本估算 (Cost Estimation)

### 4.1 使用 AutoTestDesign 工具测试的成本与效益估算

#### 4.1.1 工作量分解（基于 AutoTestDesign 工具）

| 阶段 | 工作内容 | 工作量（人时） | 负责人 |
| --- | --- | --- | --- |
| **需求结构化** | 输入自然语言需求，审查 AI 识别的 CI，修订遗漏项 | 8 | 李昊天 |
| **风险分析** | 配置风险规则，审查 AI 生成的风险评分矩阵 | 4 | 王炯昭 |
| **用例生成** | AutoTestDesign 自动生成 200+ 条用例（LLM 推理） | 2（机器时间） | 系统自动 |
| **用例审查** | 逐模块审查 AI 生成的用例，补充边缘场景 | 10 | 李昊天 + 刘逸飞 |
| **脚本转化** | 将 JSON 用例映射为 Playwright/k6 脚本 | 12 | 李宇轩 |
| **安全验证** | 手动执行高风险漏洞 PoC，补充 AI 遗漏场景 | 15 | 刘逸飞 |
| **执行与报告** | 运行自动化脚本，收集结果，生成质量报告 | 8 | 宋文轩 |
| **总计** | | **59 人时** | |

**注**："用例生成"阶段的 2 人时为机器自动执行时间，不计入人工成本。

#### 4.1.2 资源成本

| 资源类型 | 规格 | 单价 | 用量 | 小计 |
| --- | --- | --- | --- | --- |
| **LLM API 调用** | Claude 3.5 Sonnet / GPT-4o | $0.01/千 tokens | 500K tokens | $5 |
| **云服务器** | AWS t3.medium (2 vCPU, 4GB RAM) | $0.0416/小时 | 60 小时 | $2.5 |
| **测试工具许可** | Burp Suite Professional | $399/年 | 1 license | $399（一次性） |
| **团队协作工具** | GitHub Enterprise | $21/用户/月 | 5 用户 × 1 月 | $105 |
| **总计** | | | | **$511.5** |

### 4.2 与纯手工测试（Manual Testing）的显式对比

#### 4.2.1 工作量对比

| 活动 | 纯手工测试 (Manual) | AutoTestDesign 辅助 | 效率提升 |
| --- | --- | --- | --- |
| **需求分析与 CI 识别** | 40 小时（人工阅读需求文档，手动列举覆盖项） | 8 小时（AI 自动识别 + 人工审查） | **80%** ↓ |
| **测试技术选型** | 10 小时（团队讨论决定 EP/BVA/DT 应用范围） | 2 小时（AI 自动推荐 + 人工确认） | **80%** ↓ |
| **用例设计与编写** | 60 小时（手工编写 200+ 条用例，含前置条件/步骤/预期结果） | 10 小时（AI 生成 + 人工审查修订） | **83%** ↓ |
| **用例评审与优化** | 15 小时（团队会议逐条评审用例质量） | 5 小时（聚焦 AI 低置信度用例） | **67%** ↓ |
| **脚本编写** | 30 小时（手工编写 Playwright/k6 脚本） | 12 小时（基于 JSON 模板自动映射） | **60%** ↓ |
| **总工作量** | **155 人时** | **37 人时** | **76%** ↓ |

#### 4.2.2 性能目标达成情况

| 指标 | 目标值 | AutoTestDesign 实测值 | 是否达标 |
| --- | --- | --- | --- |
| **单次用例生成时间** | ≤ 2 秒 | 1.5 秒（平均，基于 Claude 3.5） | ✅ |
| **CI 识别准确率** | ≥ 85% | 88%（经人工审查修正后） | ✅ |
| **用例重复率** | ≤ 10% | 7%（去重后） | ✅ |
| **人工审查每模块耗时** | ≤ 30 分钟 | 25 分钟（平均） | ✅ |
| **总耗时缩短比例** | ≥ 60% | 76% | ✅ |

#### 4.2.3 质量对比

| 维度 | 纯手工测试 | AutoTestDesign 辅助 | 说明 |
| --- | --- | --- | --- |
| **需求覆盖率** | 75-80%（人工易遗漏边缘场景） | 95%+（AI 系统性扫描） | AI 能识别隐性依赖关系 |
| **用例一致性** | 低（不同人员风格差异大） | 高（统一模板生成） | JSON 结构标准化 |
| **安全漏洞发现率** | 依赖个人经验 | 系统化覆盖 OWASP Top 10 | 规则库保证全面性 |
| **可追溯性** | 需手工维护需求-用例映射 | 自动建立 traceability matrix | CI ID 贯穿全流程 |

### 4.3 投资回报率（ROI）分析

```
ROI = (纯手工成本 - AutoTestDesign 成本) / AutoTestDesign 成本
    = ($7,750 - $511.5) / $511.5
    = 1415%
```

**假设**：纯手工测试 155 人时 × $50/小时 = $7,750

**结论**：使用 AutoTestDesign 工具可将测试设计阶段的成本降低 76%，同时提升需求覆盖率和用例质量，投资回报率高达 1415%。

---

## 5. 测试环境与数据准备

### 5.1 环境架构

```
┌─────────────────────────────────────┐
│       Test Execution Environment    │
├─────────────────────────────────────┤
│  • Docker Container (Juice Shop)    │
│  • Browser Automation (Playwright)  │
│  • API Testing (Requests/k6)        │
│  • Security Tools (Burp Suite)      │
└─────────────────────────────────────┘
         ↓ HTTP/HTTPS
┌─────────────────────────────────────┐
│     OWASP Juice Shop Application    │
├─────────────────────────────────────┤
│  • Frontend: Angular                │
│  • Backend: Node.js + Express       │
│  • Database: SQLite (default)       │
│  • Port: 3000                       │
└─────────────────────────────────────┘
```

### 5.2 环境搭建

#### 方式一：Docker（推荐）
```bash
docker pull bkimminich/juice-shop:latest
docker run -d -p 3000:3000 --name juice-shop bkimminich/juice-shop:latest
```

#### 方式二：本地部署
```bash
git clone https://github.com/juice-shop/juice-shop.git
cd juice-shop
npm install
npm start
```

#### 方式三：在线演示（快速验证）
```
http://demo.owasp-juice.shop
```

### 5.3 测试数据准备

#### 预置账号（来自 seed 数据）

| 角色 | 邮箱 | 密码 | 用途 |
| --- | --- | --- | --- |
| **Admin** | admin@juice-sh.op | admin123 | 管理后台测试、权限提升 |
| **普通用户** | jim@juice-sh.op | ncc-1701 | 常规业务流程 |
| **会计用户** | accountant@juice-sh.op | i am an accountant | 财务相关功能 |
| **配送员** | delivery@juice-sh.op | z8rGhY3q | 订单配送流程 |
| **安全用户** | security-test@juice-sh.op | OWASPbWAF2013 | 安全测试专用 |
| **TOTP用户** | wurstbrot@juice-sh.op | [需配置 2FA] | 二次认证测试 |
| **软删除用户** | chris.pike@juice-sh.op | uss enterprise | 异常状态测试 |

#### 测试商品数据

| 商品名称 | 价格 | 特性 | 测试场景 |
| --- | --- | --- | --- |
| Apple Juice (1000ml) | €1.99 | 普通商品 | 基础购物流程 |
| Banana Juice (1000ml) | €1.99 | 普通商品 | 批量购买 |
| Eggfruit Juice (500ml) | €8.99 | 高价商品 | 支付测试 |
| OWASP SSL Advanced Fleece | €49.99 | 特殊商品 | 优惠券/折扣测试 |

#### 测试信用卡（模拟）

| 卡号 | 有效期 | CVV | 用途 |
| --- | --- | --- | --- |
| 4111 1111 1111 1111 | 12/2030 | 123 | Visa 测试卡 |
| 5500 0000 0000 0004 | 12/2030 | 456 | Mastercard 测试卡 |

---

## 6. 测试执行计划

### 6.1 阶段划分

#### 阶段一：核心功能验证（预计 10-15 小时）
**目标**：确保主要业务流程可用

| 模块 | 用例数 | 优先级 | 负责人 |
| --- | --- | --- | --- |
| 用户登录与会话（已完成） | 10 | Critical | 李昊天（需求审查）+ 李宇轩（脚本转化） |
| 用户注册 | 9 | Critical | 李昊天（需求审查）+ 李宇轩（脚本转化） |
| 密码与安全问答 | 8 | Critical | 李昊天（需求审查）+ 李宇轩（脚本转化） |
| 双因素认证 | 6 | Critical | 李昊天（需求审查）+ 李宇轩（脚本转化） |
| 商品目录与搜索 | 9 | High | 李昊天（需求审查）+ 李宇轩（脚本转化） |
| 购物车 | 9 | High | 李昊天（需求审查）+ 李宇轩（脚本转化） |
| 订单与结账 | 12 | Critical | 李昊天（需求审查）+ 李宇轩（脚本转化） |
| 支付与钱包 | 8 | Critical | 李昊天（需求审查）+ 李宇轩（脚本转化） |

**交付物**：
- 功能测试报告
- 阻塞性问题清单

#### 阶段二：安全漏洞挖掘（预计 15-20 小时）
**目标**：系统性发现安全漏洞

| 漏洞类型 | 用例数 | 优先级 | 工具 |
| --- | --- | --- | --- |
| SQL/NoSQL 注入 | 25 | Critical | Burp Suite、SQLmap（刘逸飞主导） |
| XSS（反射/存储/DOM） | 30 | Critical | Burp Suite、手动测试（刘逸飞主导） |
| 身份认证绕过 | 20 | Critical | 手动测试、自定义脚本（刘逸飞主导） |
| 访问控制缺陷 | 25 | High | 手动测试、ZAP（刘逸飞主导） |
| 文件上传漏洞 | 15 | High | 手动测试、Burp Suite（刘逸飞主导） |
| 业务逻辑漏洞 | 20 | High | 手动探索（刘逸飞 + 李昊天） |
| CSRF/SSRF | 15 | Medium | Burp Suite（刘逸飞主导） |

**交付物**：
- 安全测试报告
- 漏洞清单（含 PoC）
- 风险评级矩阵

#### 阶段三：API 与集成测试（预计 8-10 小时）
**目标**：验证 RESTful API 和第三方集成

| 测试项 | 用例数 | 优先级 |
| --- | --- | --- |
| REST API 认证 | 15 | High |
| API 参数验证 | 20 | Medium |
| 速率限制 | 10 | High |
| OAuth 集成 | 8 | Medium |
| WebSocket 通信 | 5 | Low |

**交付物**：
- API 测试报告
- Postman 集合导出

#### 阶段四：性能与兼容性（预计 5-8 小时）
**目标**：评估性能和跨平台兼容性

| 测试类型 | 场景 | 指标 |
| --- | --- | --- |
| 负载测试 | 100 并发用户 | 响应时间、吞吐量 |
| 压力测试 | 逐步增加负载 | 崩溃点、恢复能力 |
| 浏览器兼容 | 4 种主流浏览器 | UI 一致性、功能完整性 |
| 移动端适配 | 3 种屏幕尺寸 | 响应式布局 |

**交付物**：
- 性能测试报告
- 兼容性矩阵

#### 阶段五：回归测试与验收（预计 5-7 小时）
**目标**：验证修复效果，完成最终验收

| 活动 | 工作量 |
| --- | --- |
| 缺陷复测 | 根据修复数量 |
| 冒烟测试 | 核心流程全覆盖 |
| 文档整理 | 测试报告、缺陷汇总 |
| 验收评审 | 团队 Review |

**交付物**：
- 最终测试报告
- 缺陷关闭率统计
- 质量度量指标

---

## 7. 缺陷管理与报告

### 7.1 缺陷分级标准

| 级别 | 定义 | 示例 | SLA |
| --- | --- | --- | --- |
| **Critical** | 导致系统崩溃、数据丢失、严重安全漏洞 | SQL 注入绕过认证、任意文件上传 | 24 小时内修复 |
| **High** | 核心功能不可用、高危安全风险 | XSS 执行、权限提升、支付绕过 | 3 天内修复 |
| **Medium** | 次要功能缺陷、中等安全风险 | UI 错位、非关键输入校验缺失 | 1 周内修复 |
| **Low** | 轻微问题、优化建议 | 拼写错误、颜色不一致 | 下个版本修复 |

### 7.2 缺陷报告模板

```
### 缺陷编号：DEF-XXX

**关联模块**：[模块名称]  
**严重程度**：Critical/High/Medium/Low  
**缺陷类型**：[功能缺陷/安全漏洞/性能问题/兼容性问题]  

**复现步骤**：
1. [步骤 1]
2. [步骤 2]
3. [步骤 3]

**实际结果**：
[描述实际发生的情况]

**预期结果**：
[描述期望的正确行为]

**证据**：
- 截图：`screenshots/DEF-XXX_step1.png`
- 视频：`videos/DEF-XXX_reproduction.mp4`（可选）
- 请求日志：`logs/DEF-XXX_request.json`
- 响应日志：`logs/DEF-XXX_response.json`

**影响范围**：
[描述受影响的用户群体、功能模块、数据安全等]

**建议修复**：
[提供技术修复建议或参考链接]

**备注**：
[其他补充信息]
```

### 7.3 缺陷跟踪流程

```
发现缺陷 → 记录到 Jira/GitHub Issues → 分配给开发 → 修复 → 测试复测 → 关闭
     ↓                                              ↑
  每日站会同步                                  未通过则重新打开
```

---

## 8. 质量指标与验收标准

### 8.1 必须达成的指标

| 指标 | 目标值 | 计算方式 |
| --- | --- | --- |
| **用例执行率** | ≥ 95% | 已执行用例数 / 总用例数 |
| **需求覆盖率** | 100% | 已覆盖需求数 / 总需求数 |
| **Critical 缺陷修复率** | 100% | 已修复 Critical 数 / 总 Critical 数 |
| **High 缺陷修复率** | ≥ 90% | 已修复 High 数 / 总 High 数 |
| **测试通过率** | ≥ 85% | Pass 用例数 / 已执行用例数 |
| **缺陷重开率** | ≤ 10% | 重开缺陷数 / 总关闭缺陷数 |

### 8.2 交付检查清单

- [ ] 所有测试阶段完成
- [ ] 200+ 条用例执行完毕
- [ ] 所有 Critical/High 缺陷已修复并复测通过
- [ ] 测试报告完整（功能、安全、性能、兼容性）
- [ ] 缺陷清单归档（含 PoC 和修复建议）
- [ ] 自动化测试脚本可复用
- [ ] 知识转移文档（常见问题、最佳实践）

---

## 9. 风险管理与应对

### 9.1 项目风险矩阵

| 风险 | 可能性 | 影响 | 应对措施 |
| --- | --- | --- | --- |
| **环境不稳定** | 中 | 高 | 使用 Docker 隔离；准备备用环境 |
| **测试数据不足** | 低 | 中 | 提前准备 seed 数据；使用 Faker 生成 |
| **安全测试误报** | 中 | 中 | 人工验证 PoC；交叉复核 |
| **外部依赖不可用** | 高 | 低 | Mock 第三方服务；标记 Blocked |
| **时间不足** | 中 | 高 | 优先执行 Critical/High 用例；并行测试 |
| **团队技能缺口** | 低 | 中 | 提前培训；参考 OWASP 文档 |
| **工具兼容性问题** | 低 | 低 | 准备备选工具链 |

### 9.2 应急预案

#### 场景一：Juice Shop 启动失败
```bash
# 检查日志
docker logs juice-shop

# 重建容器
docker rm -f juice-shop
docker run -d -p 3000:3000 bkimminich/juice-shop

# 切换到在线演示环境
# http://demo.owasp-juice.shop
```

#### 场景二：关键缺陷无法复现
1. 记录详细环境和步骤
2. 尝试不同浏览器/设备
3. 清除缓存和 Cookie
4. 联系开发团队协助排查

#### 场景三：时间紧迫
1. 优先执行 Critical 用例（约 60 条）
2. 跳过 Low 优先级用例
3. 使用自动化脚本加速执行
4. 聚焦安全漏洞挖掘

---

## 10. 工具链与技术栈 (Chosen Testing Framework and Rationale)

### 10.1 执行框架选型与理由

#### 10.1.1 UI 自动化：Playwright

**选型理由**：
1. **多浏览器支持**：原生支持 Chromium、Firefox、WebKit，完美覆盖兼容性测试需求
2. **AutoTestDesign 无缝衔接**：
   - AutoTestDesign 导出的 JSON 用例包含 `selector`、`action`、`expected_value` 字段
   - 通过自定义转换器（`json_to_playwright.py`）可直接映射为 Playwright API 调用
   - 示例映射逻辑：
     ```python
     # AutoTestDesign 输出的 JSON 用例片段
     {
       "step": "fill_input",
       "selector": "#email",
       "value": "admin@juice-sh.op",
       "expected": "input filled successfully"
     }
     
     # 自动转换为 Playwright 脚本
     page.fill("#email", "admin@juice-sh.op")
     expect(page.locator("#email")).to_have_value("admin@juice-sh.op")
     ```
3. **自动等待机制**：内置智能等待，减少 flaky tests
4. **Trace Viewer**：提供执行轨迹回放，便于缺陷复现与调试
5. **TypeScript 原生支持**：与 Angular 前端技术栈一致，便于前端开发人员参与测试脚本维护

**替代方案对比**：
- **Selenium**：生态成熟但配置复杂，缺乏原生等待机制，与 AutoTestDesign JSON 映射需额外适配层
- **Cypress**：仅限 Chromium，不支持多标签页，不适合跨浏览器兼容性测试

#### 10.1.2 性能测试：k6

**选型理由**：
1. **开发者友好**：使用 JavaScript 编写测试脚本，学习曲线平缓
2. **AutoTestDesign 集成优势**：
   - AutoTestDesign 生成的性能测试场景可直接导出为 k6 脚本模板
   - 支持从 JSON 用例中提取并发用户数、持续时间、RPS 目标等参数
   - 示例转换流程：
     ```javascript
     // AutoTestDesign 生成的性能测试配置
     {
       "scenario": "product_list_load_test",
       "endpoint": "/rest/products",
       "vus": 100,
       "duration": "5m",
       "thresholds": {
         "http_req_duration": ["p(95)<2000"]
       }
     }
     
     // 自动转换为 k6 脚本
     import http from 'k6/http';
     export const options = {
       vus: 100,
       duration: '5m',
       thresholds: {
         http_req_duration: ['p(95)<2000']
       }
     };
     export default function () {
       http.get('http://localhost:3000/rest/products');
     }
     ```
3. **云原生架构**：支持分布式执行，可轻松扩展至数千虚拟用户
4. **指标丰富**：内置 HTTP、WebSocket、gRPC 等协议监控，输出 Prometheus 兼容格式
5. **CI/CD 友好**：轻量级二进制文件，易于集成到 GitHub Actions/GitLab CI

**替代方案对比**：
- **JMeter**：功能强大但配置复杂，XML 格式不便于与 AutoTestDesign JSON 集成
- **Artillery**：基于 Node.js，生态较小，社区支持不如 k6

### 10.2 安全测试工具链

| 工具 | 用途 | 与 AutoTestDesign 集成方式 |
| --- | --- | --- |
| **Burp Suite Professional** | 手动渗透测试、漏洞验证 | 导入 AutoTestDesign 生成的安全测试用例清单，按优先级执行 |
| **OWASP ZAP** | 自动化安全扫描 | 接收 AutoTestDesign 导出的 URL 列表和 payload 集合作为扫描目标 |
| **SQLmap** | SQL 注入深度探测 | 使用 AutoTestDesign 识别的高风险 API 端点作为 target |
| **NoSQLMap** | NoSQL 注入测试 | 同上，针对 MongoDB/SQLite 接口 |

### 10.3 辅助工具

| 类别 | 工具 | 用途 |
| --- | --- | --- |
| **代码分析** | ESLint、SonarQube | 静态代码分析，导入 AutoTestDesign 白盒建模结果 |
| **依赖审计** | npm audit、Snyk | 第三方库漏洞检测，与 AutoTestDesign A06 规则联动 |
| **报告生成** | Allure、pytest-html | 测试报告可视化，对接 AutoTestDesign 导出的执行结果 JSON |
| **版本控制** | Git + GitHub | 管理测试脚本、配置文件、文档 |

### 10.4 自动化框架示例

#### Playwright UI 测试（由 AutoTestDesign JSON 自动生成）
```
# tests/test_shopping_flow.py
# 此脚本由 AutoTestDesign 导出的 JSON 用例自动转换生成
import pytest
from playwright.sync_api import Page, expect

def test_add_to_cart(page: Page):
    """测试添加商品到购物车 - 源自 AutoTestDesign CI-ID: CART-001"""
    page.goto("http://localhost:3000")
    
    # 搜索商品（EP: 有效输入）
    page.fill("#searchQuery", "Apple Juice")
    page.click("#searchButton")
    
    # 点击第一个商品
    page.click("mat-card:first-child")
    
    # 添加到购物车
    page.click("#addToBasketButton")
    
    # 验证购物车图标显示数量（预期结果：1）
    expect(page.locator("#basketBadge")).to_have_text("1")
```

#### k6 性能测试（由 AutoTestDesign 场景配置自动生成）
```
// performance/load_test.js
// 此脚本由 AutoTestDesign 性能测试配置自动生成
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 100,
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.01']
  }
};

export default function () {
  let res = http.get('http://localhost:3000/rest/products');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 2s': (r) => r.timings.duration < 2000,
  });
  sleep(1);
}
```

---

## 11. 附录：参考资料

### 11.1 OWASP Juice Shop 官方资源
- **GitHub 仓库**：https://github.com/juice-shop/juice-shop
- **官方文档**：https://pwning.owasp-juice.shop/
- **在线演示**：http://demo.owasp-juice.shop
- **挑战列表**：https://pwning.owasp-juice.shop/companion-guide/latest/part2/score-board.html

### 11.2 OWASP 标准与指南
- **OWASP Top 10 2021**：https://owasp.org/Top10/
- **OWASP Testing Guide**：https://owasp.org/www-project-web-security-testing-guide/
- **OWASP Cheat Sheet Series**：https://cheatsheetseries.owasp.org/

### 11.3 相关文档
- **登录模块详细测试设计**：`JuiceShop登录模块详细测试设计与执行文档.md`
- **登录模块测试执行计划**：`JuiceShop登录模块测试执行计划.md`
- **IntelliTest 导出 JSON**：`docs/reqiure/*.json`

### 11.4 常用 API 端点速查

| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/rest/user/login` | POST | 用户登录 |
| `/rest/user/register` | POST | 用户注册 |
| `/rest/products` | GET | 获取商品列表 |
| `/rest/basket` | POST | 创建购物车 |
| `/rest/basket/:id` | GET | 获取购物车详情 |
| `/rest/order` | POST | 创建订单 |
| `/rest/order/history` | GET | 获取订单历史 |
| `/rest/user/reset-password` | POST | 密码重置 |
| `/rest/2fa/verify` | POST | 验证 TOTP |
| `/api/Challenges` | GET | 获取挑战列表 |

---
