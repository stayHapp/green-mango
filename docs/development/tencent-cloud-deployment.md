# 腾讯云 OpenCloudOS Docker 部署

本文记录把「知会」部署到腾讯云 OpenCloudOS 9.4 + Docker 的完整流程。沿用 `docs/development/test-deployment.md` 的部署结构，但用 Docker 替换手工 venv / systemd。

## 部署结构

```text
浏览器
  → Nginx :443（HTTPS，Let's Encrypt 证书）
      → 静态前端 /opt/zhihui-demo/app/frontend/dist
      → /api 反代 → 127.0.0.1:8010（容器 zhihui-api）→ SQLite
```

| 资源 | 路径 / 服务 |
|------|------------|
| 应用代码 | `/opt/zhihui-demo/app` |
| 后端运行环境变量 | `/opt/zhihui-demo/shared/backend.env` |
| 数据卷（SQLite） | `/opt/zhihui-demo/shared/data` |
| 后端容器 | `zhihui-api`（镜像 `zhihui-backend`） |
| Nginx 站点 | `/etc/nginx/conf.d/cssat.wenguang.top.conf` |
| TLS 证书 | Let's Encrypt（Certbot 续期） |
| 域名 A 记录 | `cssat.wenguang.top` → 腾讯云公网 IP |

## 适用范围与限制

- 适用于**新部署**与**从 CentOS 7 旧机迁出**。
- 旧机（CentOS 7 + glibc 2.17）无法直接运行 Node 20，故本方案把前端构建迁到 Docker 容器（`node:20-bookworm`）中，主机不再需要 Node。
- 演示数据由 `app.scripts.seed_demo` 生成；**严禁录入真实嘉宾个人信息**。
- 天气、POI 路线搜索需配置第三方凭据；未配置时使用现有中文降级提示。

---

## 0. 服务器前置条件

- OpenCloudOS 9.4（CentOS Stream 9 / RHEL 9 系亦可）
- 公网 IP + 域名 A 记录已指向本机
- 腾讯云安全组：放行 **TCP 80、443**
- 已安装 Docker 与 docker compose 插件

```bash
docker --version
docker compose version
```

## 1. 创建部署目录与同步代码

```bash
sudo mkdir -p /opt/zhihui-demo/{app,shared,shared/data}
sudo chown -R $USER:$USER /opt/zhihui-demo   # 当前用户可写；或保留 root 后续加 sudo

# 方式 A：Git
cd /opt/zhihui-demo/app
git init -b codexV2
git remote add origin <仓库地址>
git fetch origin && git checkout codexV2
git pull origin codexV2

# 方式 B：rsync（本机推送）
# rsync -avz --delete --exclude '.git' \
#   /Users/wenguang/project/cssat/dm/green-mango_codex/ \
#   root@<腾讯云IP>:/opt/zhihui-demo/app/
```

## 2. 后端环境变量

> 不入库。`backend.env` 只放在服务器 `/opt/zhihui-demo/shared/`，权限收紧。

```bash
sudo tee /opt/zhihui-demo/shared/backend.env >/dev/null <<'EOF'
DATABASE_URL=sqlite:////data/demo.db
SESSION_EXPIRE_HOURS=12
CORS_ORIGINS=https://cssat.wenguang.top
QWEATHER_API_HOST=<和风专属 Host>
QWEATHER_API_KEY=<和风服务端 Key>
WEATHER_CACHE_SECONDS=1800
AMAP_WEB_SERVICE_KEY=<高德 Web 服务 Key>
EOF
sudo chmod 600 /opt/zhihui-demo/shared/backend.env
```

## 3. Docker 后端镜像与运行

### 3.1 后端 Dockerfile

`backend/Dockerfile`：

```dockerfile
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8010
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
```

### 3.2 构建镜像

```bash
cd /opt/zhihui-demo/app/backend
docker build -t zhihui-backend:latest .
```

### 3.3 初始化数据库迁移

```bash
docker run --rm \
  --env-file /opt/zhihui-demo/shared/backend.env \
  -v /opt/zhihui-demo/shared/data:/data \
  zhihui-backend:latest \
  alembic upgrade head
```

### 3.4 启动后端容器

```bash
docker rm -f zhihui-api 2>/dev/null
docker run -d --name zhihui-api --restart unless-stopped \
  --env-file /opt/zhihui-demo/shared/backend.env \
  -v /opt/zhihui-demo/shared/data:/data \
  -p 127.0.0.1:8010:8010 \
  zhihui-backend:latest
docker ps | grep zhihui-api
curl -sS http://127.0.0.1:8010/api/health
```

## 4. 前端构建（容器内 Node 20）

```bash
cd /opt/zhihuang-demo/app/frontend
docker run --rm \
  -v "$PWD":/app -w /app node:20-bookworm \
  bash -c "npm ci && npm run build"
# 产物在 ./dist
```

产物路径：`/opt/zhihui-demo/app/frontend/dist`。

## 5. Nginx 与 HTTPS

### 5.1 安装 Nginx + Certbot

```bash
sudo dnf install -y nginx certbot python3-certbot-nginx
sudo systemctl enable --now nginx
```

### 5.2 部署配置

```bash
sudo cp /opt/zhihui-demo/app/deploy/nginx/cssat.wenguang.top.conf \
  /etc/nginx/conf.d/cssat.wenguang.top.conf
```

仓库配置：根目录指向 `frontend/dist`，`/api/` 反代 `127.0.0.1:8010`，并 include Let's Encrypt SSL 片段。

### 5.3 申请证书

```bash
sudo certbot --nginx -d cssat.wenguang.top
# 之后 certbot 会自动续期，可通过 systemctl list-timers 验证
systemctl list-timers | grep certbot
```

### 5.4 校验

```bash
sudo nginx -t
sudo systemctl reload nginx
curl -sS https://cssat.wenguang.top/api/health
```

## 6. 演示数据（可选）

```bash
docker run --rm -it \
  --env-file /opt/zhihui-demo/shared/backend.env \
  -v /opt/zhihui-demo/shared/data:/data \
  zhihui-backend:latest \
  python -m app.scripts.seed_demo
```

> 严禁录入真实姓名 / 手机号 / 邮箱。

## 7. 日常更新

> 服务器上操作。

```bash
cd /opt/zhihui-demo/app
git pull origin codexV2

# 后端
cd backend
docker build -t zhihui-backend:latest .
docker run --rm --env-file /opt/zhihui-demo/shared/backend.env \
  -v /opt/zhihui-demo/shared/data:/data \
  zhihui-backend:latest alembic upgrade head
docker restart zhihui-api

# 前端
cd ../frontend
docker run --rm -v "$PWD":/app -w /app node:20-bookworm \
  bash -c "npm ci && npm run build"
# nginx 自动读取 dist，无需 reload（改过 conf 才需要 nginx -t && systemctl reload nginx）
```

## 8. docker-compose（可选）

`/opt/zhihui-demo/app/deploy/docker-compose.yml`：

```yaml
services:
  api:
    build:
      context: ../backend
      dockerfile: Dockerfile
    image: zhihui-backend:latest
    container_name: zhihui-api
    restart: unless-stopped
    env_file: /opt/zhihui-demo/shared/backend.env
    volumes:
      - /opt/zhihui-demo/shared/data:/data
    ports:
      - "127.0.0.1:8010:8010"
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:8010/api/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

```bash
cd /opt/zhihui-demo/app/deploy
docker compose build api
docker compose run --rm api alembic upgrade head
docker compose up -d api
```

## 9. 故障排查

| 现象 | 排查方式 |
|------|----------|
| 502 Bad Gateway | `docker ps` 确认 zhihui-api 运行中；`docker logs zhihui-api` |
| /api/health 不可达 | 容器内：`docker exec -it zhihui-api curl -sS http://127.0.0.1:8010/api/health` |
| 数据库迁移失败 | 手工跑：`docker run --rm --env-file backend.env -v data:/data zhihui-backend alembic upgrade head` |
| 前端 dist 不更新 | 检查挂载路径；`ls -l /opt/zhihui-demo/app/frontend/dist/index.html` |
| 证书过期 | `sudo certbot renew`；`systemctl list-timers | grep certbot` |
| 启动即报 500 | 后端日志 `docker logs zhihui-api --tail 200`；检查 `backend.env` 必需字段 |
| 第三方接口失败 | 日志会输出 WARNING / EXCEPTION；weather.py 已经有 logger 区分 HTTP/网络/业务错误 |

## 10. 安全要求

- 不在仓库中保存服务器密码、SSH Key、数据库密钥或第三方服务凭据。
- `backend.env` 权限 600，所有者为 root。
- 演示数据库不要混用真实个人信息。
- 修改 Nginx 前先 `nginx -t` 校验；改后端前先构建镜像验证。
- 域名白名单 `CORS_ORIGINS` 必须与实际访问域名一致。

## 11. 切换域名 / 迁出旧机

1. 在域名解析商修改 A 记录，把 `cssat.wenguang.top` → 腾讯云新公网 IP  
2. 旧机保留一段时间以便回滚  
3. 腾讯云安全组放行 80/443（入站）  
4. 证书在腾讯云机器重新签发：`sudo certbot --nginx -d cssat.wenguang.top`
