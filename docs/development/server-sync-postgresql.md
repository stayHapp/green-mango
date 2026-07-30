# 无 Git 服务器 Docker 更新部署（PostgreSQL）

本文参照 `docs/development/tencent-cloud-deployment.md` 的部署结构，记录当前服务器已经用 Docker 启动服务后，如何从本地同步代码并更新服务。

当前场景：

- 服务器没有 Git。
- 服务器已经有 Docker 环境，并已启动后端容器。
- 数据库使用 PostgreSQL，不再使用旧文档中的 SQLite。
- 代码从本地通过 `rsync` 推送到服务器。

## 部署结构

```text
浏览器
  → Nginx :443
      → 静态前端 /opt/zhihui-demo/app/frontend/dist
      → /api 反代 → 127.0.0.1:8010（容器 zhihui-api）
          → PostgreSQL 127.0.0.1:5432
```

| 资源 | 路径 / 服务 |
| --- | --- |
| 应用代码 | `/opt/zhihui-demo/app` |
| 后端环境变量 | `/opt/zhihui-demo/shared/backend.env` |
| 后端镜像 | `zhihui-backend:latest` |
| 后端容器 | `zhihui-api` |
| 后端监听 | `127.0.0.1:8010` |
| PostgreSQL 数据库 | `green_mango` |
| PostgreSQL 用户 | `green_mango_user` |
| Nginx 站点 | `/etc/nginx/conf.d/cssat.wenguang.top.conf` |
| 前端产物 | `/opt/zhihui-demo/app/frontend/dist` |

## 1. PostgreSQL 配置

服务器后端环境变量文件为：

```bash
/opt/zhihui-demo/shared/backend.env
```

PostgreSQL 连接串应使用服务器上已验证通过的配置：

```env
DATABASE_URL=postgresql+psycopg://green_mango_user:替换为服务器数据库密码@127.0.0.1:5432/green_mango
SESSION_EXPIRE_HOURS=12
CORS_ORIGINS=https://cssat.wenguang.top
QWEATHER_API_HOST=
QWEATHER_API_KEY=
WEATHER_CACHE_SECONDS=1800
AMAP_WEB_SERVICE_KEY=
```

权限建议：

```bash
sudo chmod 600 /opt/zhihui-demo/shared/backend.env
```

### 1.1 容器访问 PostgreSQL 的方式

本文推荐后端容器使用 `--network host`。

这样容器和宿主机共用网络，容器内访问：

```text
127.0.0.1:5432
```

就是访问宿主机 PostgreSQL。因此 `DATABASE_URL` 可以继续使用 `127.0.0.1`。

如果不用 `--network host`，而使用 Docker bridge 网络，`127.0.0.1` 会指向容器自身，需要改成 `host.docker.internal` 或同一 Docker 网络内的 PostgreSQL 服务名；此方式当前不推荐。

### 1.2 Ident 认证失败处理

如果连接 PostgreSQL 时报错：

```text
FATAL:  Ident authentication failed for user "green_mango_user"
```

说明 PostgreSQL 的 `pg_hba.conf` 对本机连接使用了 `ident`，没有使用密码认证。

查询配置文件位置：

```bash
sudo -u postgres psql -tAc "SHOW hba_file;"
```

编辑该文件，例如：

```bash
sudo vi /var/lib/pgsql/data/pg_hba.conf
```

在其他 `127.0.0.1/32` 和 `::1/128` 规则之前加入或调整为：

```conf
host    green_mango    green_mango_user    127.0.0.1/32    scram-sha-256
host    green_mango    green_mango_user    ::1/128         scram-sha-256
```

重新设置密码：

```bash
sudo -u postgres psql -c "ALTER USER green_mango_user WITH PASSWORD '替换为服务器数据库密码';"
```

重新加载 PostgreSQL：

```bash
sudo systemctl reload postgresql
```

如果服务名不是 `postgresql`，先查询：

```bash
systemctl list-units | grep postgres
```

也可以用 SQL reload：

```bash
sudo -u postgres psql -c "SELECT pg_reload_conf();"
```

验证连接：

```bash
psql "postgresql://green_mango_user:替换为服务器数据库密码@127.0.0.1:5432/green_mango" -c "SELECT 1;"
```

## 2. 本地同步代码到服务器

服务器没有 Git，代码从本地通过 `rsync` 推送。

本地先检查：

```bash
cd /Users/wenguang/project/dm/green-mango
git status --short --branch
backend/.venv/bin/pytest -q
cd frontend && npm run build
```

建议先提交当前要发布的变更，方便确认同步版本。

### 2.1 服务器备份

在服务器执行：

```bash
sudo cp -a /opt/zhihui-demo/app "/opt/zhihui-demo/app.backup.$(date +%Y%m%d%H%M%S)"
docker image inspect zhihui-backend:latest >/dev/null 2>&1 && \
  docker tag zhihui-backend:latest "zhihui-backend:rollback-$(date +%Y%m%d%H%M%S)"
```

### 2.2 本地预演同步

在本地执行：

```bash
rsync -avz --delete --dry-run \
  --exclude ".git" \
  --exclude "backend/.env" \
  --exclude "backend/.venv" \
  --exclude "backend/dev.db" \
  --exclude "frontend/node_modules" \
  --exclude "frontend/dist" \
  /Users/wenguang/project/dm/green-mango/ \
  root@服务器IP:/opt/zhihui-demo/app/
```

确认输出只包含本次要更新的文件后，再正式同步。

### 2.3 本地正式同步

```bash
rsync -avz --delete \
  --exclude ".git" \
  --exclude "backend/.env" \
  --exclude "backend/.venv" \
  --exclude "backend/dev.db" \
  --exclude "frontend/node_modules" \
  --exclude "frontend/dist" \
  /Users/wenguang/project/dm/green-mango/ \
  root@服务器IP:/opt/zhihui-demo/app/
```

注意：

- 不同步 `.git`。
- 不同步本地 `backend/.env`。
- 不同步本地虚拟环境、前端依赖和构建产物。
- `--delete` 会删除服务器上本地不存在的文件，因此必须先备份并预演。

## 3. 后端 Docker 更新

### 3.1 确认 Dockerfile

后端镜像构建依赖：

```bash
/opt/zhihui-demo/app/backend/Dockerfile
```

仓库已经包含 `backend/Dockerfile` 和 `backend/.dockerignore`。正常执行 rsync 后，服务器 `backend/` 目录下应存在该文件。可以在服务器检查：

```bash
ls -l /opt/zhihui-demo/app/backend/Dockerfile
```

如果服务器仍报错：

```text
open Dockerfile: no such file or directory
```

说明本次代码同步没有把 `backend/Dockerfile` 同步到服务器，应先检查 rsync 源路径和排除规则。

Dockerfile 内容：

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ARG PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./

RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-deps --no-build-isolation .

EXPOSE 8010
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
```

依赖安装层只受 `pyproject.toml` 和 `requirements.txt` 影响。日常只修改业务代码或迁移文件时，Docker 会复用已安装依赖，不需要重新下载 Python 包。

### 3.2 数据库连通性预检

构建和迁移前先在服务器确认 PostgreSQL 正常监听，避免后端容器启动后才从日志看到 `Connection refused`。

```bash
systemctl list-units | grep postgres
ss -lntp | grep 5432
psql "postgresql://green_mango_user:替换为服务器数据库密码@127.0.0.1:5432/green_mango" -c "SELECT 1;"
```

如果 `ss` 没有看到 `5432`，说明 PostgreSQL 没有启动或没有监听 TCP 端口。先按实际服务名启动，例如：

```bash
sudo systemctl start postgresql
# 或使用实际服务名，例如 sudo systemctl start postgresql-16
```

如果 `psql` 本机连接失败，先修复 PostgreSQL 服务、数据库用户、密码或 `pg_hba.conf`，不要继续重建后端容器。

### 3.3 构建新镜像

在服务器执行：

```bash
cd /opt/zhihui-demo/app/backend
docker build -t zhihui-backend:latest .
```

### 3.4 执行数据库迁移

每次更新都执行迁移；没有新迁移时不会改变数据库。

```bash
docker run --rm \
  --network host \
  --env-file /opt/zhihui-demo/shared/backend.env \
  zhihui-backend:latest \
  alembic upgrade head
```

迁移必须带 `--network host`。如果漏掉该参数，容器内的 `127.0.0.1:5432` 会指向容器自身，通常会报 `Connection refused`。

### 3.5 重建后端容器

不要只执行：

```bash
docker restart zhihui-api
```

原因：`docker restart` 只会重启旧容器，不会让旧容器使用刚构建的新镜像。

正确方式是删除旧容器，并用新镜像重建：

```bash
docker rm -f zhihui-api 2>/dev/null || true
docker run -d --name zhihui-api --restart unless-stopped \
  --network host \
  --env-file /opt/zhihui-demo/shared/backend.env \
  zhihui-backend:latest \
  uvicorn app.main:app --host 127.0.0.1 --port 8010
```

重建后确认容器网络模式为 `host`：

```bash
docker inspect zhihui-api --format '{{.HostConfig.NetworkMode}}'
```

输出应为：

```text
host
```

## 4. 前端更新

### 4.1 服务器容器内构建

如果服务器可以拉取 Node 镜像，在服务器执行：

```bash
cd /opt/zhihui-demo/app/frontend
docker run --rm \
  -v "$PWD":/app \
  -w /app \
  node:20-bookworm \
  bash -c "npm ci && npm run build"
```

构建产物在：

```bash
/opt/zhihui-demo/app/frontend/dist
```

Nginx 直接读取该目录，Nginx 配置未变化时不需要 reload。

### 4.2 本地构建后同步 dist

如果服务器无法拉取 Node 镜像，可以在本地构建前端后只同步 `dist`：

```bash
cd /Users/wenguang/project/dm/green-mango/frontend
npm ci
npm run build
rsync -avz --delete \
  /Users/wenguang/project/dm/green-mango/frontend/dist/ \
  root@服务器IP:/opt/zhihui-demo/app/frontend/dist/
```

## 5. 更新后验证

服务器执行：

```bash
docker ps | grep zhihui-api
docker logs zhihui-api --tail 100
curl -sS http://127.0.0.1:8010/api/health
curl -sS https://cssat.wenguang.top/api/health
```

浏览器验证：

- 管理员登录。
- 嘉宾登录。
- 工作人员登录。
- 工作人员扫码或手工签到。
- 嘉宾端签到状态约 3 秒内刷新。

## 6. 回滚

如果更新后后端异常，优先用更新前保留的 rollback 镜像恢复。

先查看可用回滚镜像：

```bash
docker images | grep zhihui-backend
```

使用指定 rollback 镜像重建容器：

```bash
docker rm -f zhihui-api 2>/dev/null || true
docker run -d --name zhihui-api --restart unless-stopped \
  --network host \
  --env-file /opt/zhihui-demo/shared/backend.env \
  zhihui-backend:rollback-替换为具体时间戳 \
  uvicorn app.main:app --host 127.0.0.1 --port 8010
```

如果需要代码目录一起回滚：

```bash
sudo mv /opt/zhihui-demo/app "/opt/zhihui-demo/app.failed.$(date +%Y%m%d%H%M%S)"
sudo cp -a /opt/zhihui-demo/app.backup.备份时间 /opt/zhihui-demo/app
```

注意：如果已经执行了新的数据库迁移，代码回滚前必须确认旧代码是否兼容当前数据库结构。当前项目没有自动数据库回滚流程，真实数据环境不要轻易执行破坏性数据库回滚。

## 7. 常见问题

| 现象 | 处理方式 |
| --- | --- |
| `open Dockerfile: no such file or directory` | `/opt/zhihui-demo/app/backend` 下缺少 Dockerfile，检查 rsync 是否同步了 `backend/Dockerfile` |
| `Ident authentication failed` | 按本文 1.2 修改 `pg_hba.conf`，改为密码认证 |
| PostgreSQL `Connection refused` | 先确认 `ss -lntp | grep 5432` 有监听，再确认迁移和后端容器都使用了 `--network host` |
| 构建了新镜像但服务没更新 | 不要只 `docker restart`；需要 `docker rm -f zhihui-api` 后重新 `docker run` |
| `/api/health` 不通 | 查看 `docker ps` 和 `docker logs zhihui-api --tail 100` |
| 前端页面没更新 | 确认 `frontend/dist/index.html` 更新时间；必要时清浏览器缓存 |

## 8. 安全要求

- 不把服务器 `backend.env`、数据库密码、SSH Key、第三方服务 Key 写入仓库。
- `/opt/zhihui-demo/shared/backend.env` 权限保持 `600`。
- PostgreSQL 不对公网开放，只允许本机或必要内网访问。
- Nginx 只反代 `/api/` 到本机后端端口。
- 测试环境不要保存真实嘉宾个人信息。
