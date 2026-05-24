# 成员 E：Docker 容器化部署说明

## 1. 部署目标

本项目通过 Docker Compose 同时启动前端与后端服务，降低本地环境差异带来的部署成本。部署完成后，开发者只需要安装 Docker Desktop，并准备后端环境变量文件，即可在本机运行 IntelliTest。

该部署方式属于本地容器化部署，不等同于公网服务器部署。容器启动后，服务默认只通过本机端口暴露：

- 前端访问地址：http://localhost:3000
- 后端接口地址：http://localhost:8000
- 后端接口文档：http://localhost:8000/docs

## 2. 前置条件

1. 已安装 Docker Desktop。
2. Docker Desktop 已启动，并处于 Running 状态。
3. 项目根目录存在 `backend/.env` 文件。
4. `backend/.env` 中至少配置可用的大模型 API 参数，例如：

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=你的真实 API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DATABASE_URL=sqlite:///./app.db
```

注意：`.env` 文件不应提交到 Git 仓库。当前 Docker 配置只会把 `backend/.env` 注入后端容器，前端容器只接收 `API_PROXY_TARGET`，避免把后端 API Key 放入不需要使用它的容器环境。

## 3. 启动命令

在项目根目录执行：

```powershell
docker compose up --build
```

首次执行时 Docker 会构建镜像并下载依赖，耗时会比较久。后续如果只启动已构建好的容器，可以执行：

```powershell
docker compose up
```

如果希望后台运行：

```powershell
docker compose up -d --build
```

## 4. 停止与清理

停止容器：

```powershell
docker compose down
```

停止并删除匿名卷：

```powershell
docker compose down -v
```

查看运行状态：

```powershell
docker compose ps
```

查看日志：

```powershell
docker compose logs -f
```

只查看后端日志：

```powershell
docker compose logs -f backend
```

只查看前端日志：

```powershell
docker compose logs -f frontend
```

## 5. 部署成功的预期结果

执行 `docker compose up --build` 后，应看到两个服务启动：

- `intellitest-backend`
- `intellitest-frontend`

后端健康检查通过后，前端容器会继续启动。浏览器访问 `http://localhost:3000` 应显示 IntelliTest 前端页面；访问 `http://localhost:8000/docs` 应显示 FastAPI Swagger 文档。

## 6. 部署后测试流程

建议按以下顺序测试：

1. 打开 `http://localhost:8000/health`。
   - 预期结果：返回 `{"status":"ok"}`。

2. 打开 `http://localhost:8000/docs`。
   - 预期结果：可以看到后端 API 文档。

3. 打开 `http://localhost:3000`。
   - 预期结果：可以看到 IntelliTest 前端页面，右上角显示在线状态。

4. 在“需求输入”页面输入一条完整需求并解析。
   - 预期结果：需求出现在需求列表中。

5. 对需求执行结构化。
   - 预期结果：状态变为已结构化。

6. 执行风险分析。
   - 预期结果：风险面板展示风险分数和优先级。

7. 进入黑盒测试生成测试用例。
   - 预期结果：生成 EP、BVA、DT 或组合测试用例。

8. 进入测试预言页面生成或校验预期结果。
   - 预期结果：页面展示推理步骤、一致性状态和预期结果。

9. 进入审查导出页面导出 JSON、CSV、Excel。
   - 预期结果：浏览器下载对应文件，文件包含测试用例、需求风险信息和覆盖项。取消勾选“需求与风险”或“覆盖项”后，导出文件应按勾选范围裁剪。

## 7. 常见问题

### 7.1 Docker 拉取镜像很慢或失败

当前 `docker-compose.yml` 默认使用 Dockerfile 中的官方基础镜像：

- `python:3.12-slim`
- `node:20-alpine`

如果拉取失败，通常是 Docker Hub 网络连接或本机镜像源配置问题。可以稍后重试，或在 Docker Desktop 中配置可用的镜像加速源。

本项目也支持临时覆盖基础镜像，不需要修改仓库文件。例如在 PowerShell 中执行：

```powershell
$env:PYTHON_IMAGE="可用镜像源/library/python:3.12-slim"
$env:NODE_IMAGE="可用镜像源/library/node:20-alpine"
docker compose up --build -d
```

不要把需要登录授权的第三方镜像源直接写死到项目配置中，否则其他组员可能无法构建。

### 7.2 后端容器启动失败，提示缺少 API Key

检查 `backend/.env` 是否存在，并确认其中的大模型 API Key 可用。

### 7.3 前端可以打开，但接口请求失败

检查后端容器是否健康：

```powershell
docker compose ps
```

也可以查看后端日志：

```powershell
docker compose logs -f backend
```

### 7.4 修改代码后是否需要重新构建

当前 Compose 配置挂载了前端 `src` 与后端代码目录，因此开发时多数代码修改会热更新。若修改依赖文件，例如 `requirements.txt`、`package.json`、`package-lock.json` 或 Dockerfile，需要重新构建：

```powershell
docker compose up --build
```

## 8. 交付说明

该容器化方案用于成员 E 的部署与交付支持，目标是提供统一、可复现的本地运行方式。组员或验收人员克隆仓库后，只要准备自己的 `backend/.env`，即可使用同一套 Docker Compose 命令在本地启动完整系统。
