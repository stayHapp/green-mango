# 新服务器与新域名部署

本文记录把「知会」部署到新服务器 `49.233.60.2`，暂定绑定域名 `meeting.cssat.cn`，并从旧服务器迁移数据的操作流程。

## 已确认信息

| 项目 | 当前值 |
| --- | --- |
| 暂定域名 | `meeting.cssat.cn` |
| 新服务器公网 IP | `49.233.60.2` |
| 服务器系统 | TencentOS Server |
| SSH 用户 | `tian` |
| SSH 端口 | `22` |
| Docker | 已安装 |
| PostgreSQL | 已安装，版本 `16.6` |
| 数据策略 | 从旧服务器迁移数据库和附件 |
| 域名备案 | 已备案 |
| 天气和地图 Key | 已有 |
| 部署目录 | `/opt/green-mango` |

## 仍需确认

- 同事是否已经为 `meeting.cssat.cn` 添加 DNS 记录。
- 旧服务器 SSH 地址、用户和旧数据库连接信息。
- 旧服务器会议资料附件目录，通常是旧 `backend.env` 中的 `MATERIAL_STORAGE_DIR`。
- 新服务器 PostgreSQL 的数据库密码，不应写入仓库或聊天记录。
- 新服务器未安装 Nginx，且已有 Docker Web 服务占用公网 `80`。
- 新服务器是否已安装 Certbot、Node 构建环境；如果没有，按最终入口方案补齐。

## 目标部署结构

```text
浏览器
  → https://meeting.cssat.cn
      → 统一公网入口 :443
          → 静态前端 /opt/green-mango/app/frontend/dist
          → /api 反代 → 127.0.0.1:8010（Docker 容器 zhihui-api）
              → PostgreSQL 16.6 127.0.0.1:5432
```

| 资源 | 路径 / 名称 |
| --- | --- |
| 应用代码 | `/opt/green-mango/app` |
| 共享配置 | `/opt/green-mango/shared` |
| 后端环境变量 | `/opt/green-mango/shared/backend.env` |
| 会议资料附件 | `/opt/green-mango/shared/materials` |
| PostgreSQL 数据库 | `green_mango` |
| PostgreSQL 用户 | `green_mango_user` |
| 后端镜像 | `zhihui-backend:latest` |
| 后端容器 | `zhihui-api` |
| 后端监听 | `127.0.0.1:8010` |
| 公网入口 | 待统一入口方案确认后配置 |

## 1. 让同事新增域名记录

请同事在 `cssat.cn` 的 DNS 控制台新增：

```text
类型：A
主机记录：meeting
记录值：49.233.60.2
```

生效后，本地或服务器执行：

```bash
dig +short meeting.cssat.cn
```

期望输出包含：

```text
49.233.60.2
```

如果 DNS 尚未生效，可以先用公网 IP 完成服务器内部配置，但 HTTPS 证书必须等域名解析生效后再申请。

## 2. 检查新服务器基础状态

本地连接服务器：

```bash
ssh tian@49.233.60.2
```

在服务器执行：

```bash
cat /etc/os-release
docker --version
psql --version
systemctl status postgresql --no-pager
command -v nginx || true
command -v certbot || true
```

如果 PostgreSQL 服务名不是 `postgresql`，查询实际名称：

```bash
systemctl list-units | grep -i postgres
```

当前服务器未安装 Nginx，且已有 Docker Web 服务占用公网 `80`。不要直接安装并启动宿主机 Nginx；公网入口按第 3 节确定后再配置。

确认安全组或防火墙放行：

| 端口 | 用途 |
| --- | --- |
| `22/tcp` | SSH |
| `80/tcp` | HTTP 与证书申请 |
| `443/tcp` | HTTPS |

不要向公网开放 `5432` 和 `8010`。

## 3. 公网入口方案

当前服务器已有 `pata-showcase-web-1` 容器占用公网 `80` 端口，宿主机未安装 Nginx。因此本项目不能直接启动宿主机 Nginx 监听 `80/443`，否则会影响现有服务。

本次部署建议采用以下二选一方案：

1. 推荐方案：将 `pata-showcase-web-1` 和本项目纳入统一反向代理，由统一入口按域名转发旧服务和 `meeting.cssat.cn`。
2. 临时方案：本项目先只在服务器本机监听后端端口和构建前端，等统一公网入口确定后再开放正式域名。

如果最终采用统一 Nginx 入口，需要先安排维护窗口，将 `pata-showcase-web-1` 从宿主机 `80` 改为内网端口或仅 Docker 内部端口，再由 Nginx 转发到该旧服务和本项目。该变更涉及其他业务，不在本文自动执行命令中直接操作。

如果 `pata-showcase-web-1` 本身可作为按域名转发的入口，则可以把 `meeting.cssat.cn` 接入该容器的配置，而不额外引入宿主机 Nginx。

本项目内部端口默认使用：

| 用途 | 地址 |
| --- | --- |
| 后端 API | `127.0.0.1:8010` |
| 前端静态目录 | `/opt/green-mango/app/frontend/dist` |

如果 `8010` 与现有服务冲突，统一改用 `8011`，并同步修改后端启动端口和公网入口的反向代理目标。

- 后端只绑定 `127.0.0.1`，不要绑定 `0.0.0.0` 对公网开放。

## 4. 检查项目同步是否完整

你已经把项目同步到了新服务器。先确认目录结构：

```bash
ls -la /opt/green-mango
ls -la /opt/green-mango/app
ls -la /opt/green-mango/app/backend
ls -la /opt/green-mango/app/frontend
```

关键文件必须存在：

```bash
test -f /opt/green-mango/app/backend/Dockerfile
test -f /opt/green-mango/app/backend/alembic.ini
test -d /opt/green-mango/app/backend/alembic/versions
test -f /opt/green-mango/app/frontend/package.json
test -f /opt/green-mango/app/frontend/vite.config.ts
test -f /opt/green-mango/app/scripts/check_all.sh
```

如果某条 `test` 命令没有输出，表示通过；如果报错，说明同步不完整，需要从本机重新同步。

本机重新同步示例：

```bash
rsync -avz --delete \
  --exclude ".git" \
  --exclude "backend/.env" \
  --exclude "backend/.venv" \
  --exclude "backend/dev.db" \
  --exclude "frontend/node_modules" \
  --exclude "frontend/dist" \
  /Users/wenguang/project/dm/green-mango/ \
  tian@49.233.60.2:/opt/green-mango/app/
```

## 5. 准备持久目录

在新服务器执行：

```bash
sudo mkdir -p /opt/green-mango/app
sudo mkdir -p /opt/green-mango/shared/materials
sudo chown -R tian:tian /opt/green-mango
```

`/opt/green-mango/shared` 用于保存服务器私有配置和附件，不应被代码同步覆盖。

## 6. 准备 PostgreSQL 16.6

先确认 PostgreSQL 监听本机端口：

```bash
ss -lntp | grep 5432
```

创建数据库和用户。真实密码请在服务器本地生成并保存到安全位置，不要写入仓库：

```bash
openssl rand -base64 32
```

将下面命令中的 `替换为新数据库密码` 换成真实密码：

```bash
sudo -u postgres psql <<'SQL'
CREATE DATABASE green_mango;
CREATE USER green_mango_user WITH PASSWORD '替换为新数据库密码';
GRANT ALL PRIVILEGES ON DATABASE green_mango TO green_mango_user;
\c green_mango
GRANT ALL ON SCHEMA public TO green_mango_user;
SQL
```

如果数据库或用户已存在，用以下方式检查：

```bash
sudo -u postgres psql -c "\l" | grep green_mango
sudo -u postgres psql -c "\du" | grep green_mango_user
```

验证密码连接：

```bash
psql "postgresql://green_mango_user:替换为新数据库密码@127.0.0.1:5432/green_mango" -c "SELECT 1;"
```

如果出现 `Ident authentication failed`，查询并编辑 `pg_hba.conf`：

```bash
sudo -u postgres psql -tAc "SHOW hba_file;"
```

在其他 `127.0.0.1/32` 和 `::1/128` 规则之前加入：

```conf
host    green_mango    green_mango_user    127.0.0.1/32    scram-sha-256
host    green_mango    green_mango_user    ::1/128         scram-sha-256
```

重新加载 PostgreSQL：

```bash
sudo systemctl reload postgresql
```

如果服务名不是 `postgresql`，改用实际服务名。

## 7. 迁移旧服务器数据库

因为本次要从旧服务器迁移数据，不要直接用空库上线。

### 7.1 从旧服务器导出

在旧服务器执行。以下连接串需要换成旧服务器真实配置，可从旧服务器的 `backend.env` 中查看：

```bash
pg_dump -Fc \
  "postgresql://旧数据库用户:旧数据库密码@127.0.0.1:5432/旧数据库名" \
  -f /tmp/green_mango.dump
```

如果旧服务器后端还在写入数据，正式迁移前应先安排停机窗口，停止旧后端服务后再导出，避免漏数据。

### 7.2 复制 dump 到新服务器

在本地或旧服务器执行：

```bash
scp /tmp/green_mango.dump tian@49.233.60.2:/tmp/green_mango.dump
```

### 7.3 在新服务器恢复

在新服务器执行：

```bash
pg_restore --clean --if-exists \
  -d "postgresql://green_mango_user:替换为新数据库密码@127.0.0.1:5432/green_mango" \
  /tmp/green_mango.dump
```

恢复后检查表和迁移版本：

```bash
psql "postgresql://green_mango_user:替换为新数据库密码@127.0.0.1:5432/green_mango" -c "\dt"
psql "postgresql://green_mango_user:替换为新数据库密码@127.0.0.1:5432/green_mango" -c "SELECT version_num FROM alembic_version;"
```

## 8. 迁移会议资料附件

旧服务器附件目录以旧 `backend.env` 的 `MATERIAL_STORAGE_DIR` 为准。如果旧服务器未显式配置，项目默认可能是后端运行目录下的 `./data/meeting-materials`。

从旧服务器同步到新服务器：

```bash
rsync -avz \
  旧服务器用户@旧服务器IP:旧服务器附件目录/ \
  /opt/green-mango/shared/materials/
```

如果在新服务器上从本地发起同步，也可以先把附件拉到本地再推送。完成后检查：

```bash
find /opt/green-mango/shared/materials -type f | head
sudo chown -R tian:tian /opt/green-mango/shared/materials
```

## 9. 配置后端环境变量

在新服务器创建 `/opt/green-mango/shared/backend.env`：

```bash
sudo tee /opt/green-mango/shared/backend.env >/dev/null <<'EOF'
DATABASE_URL=postgresql+psycopg://green_mango_user:替换为新数据库密码@127.0.0.1:5432/green_mango
SESSION_EXPIRE_HOURS=12
CORS_ORIGINS=https://meeting.cssat.cn
QWEATHER_API_HOST=替换为和风天气Host
QWEATHER_API_KEY=替换为和风天气Key
WEATHER_CACHE_SECONDS=1800
AMAP_WEB_SERVICE_KEY=替换为高德Web服务Key
MATERIAL_STORAGE_DIR=/opt/green-mango/shared/materials
MATERIAL_MAX_FILE_BYTES=20971520
EOF
sudo chmod 600 /opt/green-mango/shared/backend.env
```

注意：

- `backend.env` 不提交到仓库。
- 如果 `meeting.cssat.cn` 最终变更，`CORS_ORIGINS` 要同步改成最终域名。
- 如果需要同时兼容旧域名和新域名，`CORS_ORIGINS` 可用英文逗号分隔多个来源。

## 10. 构建后端并升级数据库

在新服务器执行：

```bash
cd /opt/green-mango/app/backend
docker build -t zhihui-backend:latest .
```

用当前代码把迁移升级到最新版本：

```bash
docker run --rm \
  --network host \
  --env-file /opt/green-mango/shared/backend.env \
  zhihui-backend:latest \
  alembic upgrade head
```

启动后端容器：

```bash
docker rm -f zhihui-api 2>/dev/null || true
docker run -d --name zhihui-api --restart unless-stopped \
  --network host \
  --env-file /opt/green-mango/shared/backend.env \
  zhihui-backend:latest \
  uvicorn app.main:app --host 127.0.0.1 --port 8010
```

验证：

```bash
docker ps | grep zhihui-api
docker inspect zhihui-api --format '{{.HostConfig.NetworkMode}}'
docker logs zhihui-api --tail 100
curl -sS http://127.0.0.1:8010/api/health
```

网络模式应输出：

```text
host
```

如果第 3 节确认 `zhihui-api` 名称或 `8010` 端口已被占用，必须先替换本节命令中的容器名或端口，再执行删除和启动命令。

## 11. 配置并构建前端

在新服务器创建 `/opt/green-mango/app/frontend/.env.production`：

```bash
cat >/opt/green-mango/app/frontend/.env.production <<'EOF'
VITE_API_BASE_URL=/api
VITE_PUBLIC_APP_URL=https://meeting.cssat.cn
EOF
```

`VITE_PUBLIC_APP_URL` 会影响管理员端生成会议入口链接和二维码。域名最终变更时，必须重新构建前端。

使用 Docker Node 镜像构建：

```bash
cd /opt/green-mango/app/frontend
docker run --rm \
  -v "$PWD":/app \
  -w /app \
  node:20-bookworm \
  bash -c "npm ci && npm run build"
```

确认产物：

```bash
test -f /opt/green-mango/app/frontend/dist/index.html
ls -lh /opt/green-mango/app/frontend/dist
```

## 12. 配置公网入口

本节必须在第 3 节的公网入口方案确定后执行。当前 `pata-showcase-web-1` 已占用宿主机 `80`，不要直接启动宿主机 Nginx。

### 12.1 统一 Nginx 入口配置示例

只有在维护窗口内完成旧服务接入统一 Nginx 后，才使用本示例。

```bash
sudo tee /etc/nginx/conf.d/meeting.cssat.cn.conf >/dev/null <<'EOF'
server {
    listen 80;
    server_name meeting.cssat.cn;

    root /opt/green-mango/app/frontend/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF
sudo nginx -t
sudo systemctl reload nginx
```

reload 后立即验证旧服务仍正常：

```bash
curl -I https://旧服务域名
```

验证：

```bash
curl -I http://meeting.cssat.cn
curl -sS http://meeting.cssat.cn/api/health
```

### 12.2 HTTPS 证书

统一入口确定、DNS 生效且 `80` 端口能正确响应 `meeting.cssat.cn` 后，再申请证书：

```bash
sudo certbot --nginx -d meeting.cssat.cn
```

完成后验证：

```bash
sudo nginx -t
sudo systemctl reload nginx
systemctl list-timers | grep certbot
curl -sS https://meeting.cssat.cn/api/health
```

如果最终域名不是 `meeting.cssat.cn`，需要把 Nginx 配置、Certbot 域名、后端 `CORS_ORIGINS` 和前端 `VITE_PUBLIC_APP_URL` 全部替换成最终域名。

## 13. 切换前最终核对

在新服务器执行：

```bash
docker ps | grep zhihui-api
docker logs zhihui-api --tail 100
curl -sS http://127.0.0.1:8010/api/health
curl -sS https://meeting.cssat.cn/api/health
```

数据库核对：

```bash
psql "postgresql://green_mango_user:替换为新数据库密码@127.0.0.1:5432/green_mango" -c "SELECT COUNT(*) FROM meetings;"
psql "postgresql://green_mango_user:替换为新数据库密码@127.0.0.1:5432/green_mango" -c "SELECT COUNT(*) FROM guests;"
psql "postgresql://green_mango_user:替换为新数据库密码@127.0.0.1:5432/green_mango" -c "SELECT COUNT(*) FROM users;"
```

浏览器核对：

- 打开 `https://meeting.cssat.cn`。
- 管理员可以登录。
- 管理员能看到迁移过来的会议。
- 管理员生成的会议入口链接和二维码使用 `meeting.cssat.cn`。
- 嘉宾可以登录并查看资料、会议服务和二维码。
- 工作人员可以登录并看到负责会议。
- 工作人员扫码或手工签到可用。
- 管理员签到统计和导出可用。
- 会议资料附件可下载。
- 刷新前端子页面不会 404。

## 14. 正式迁移建议顺序

为避免旧服务器仍有新数据写入，正式切换建议按以下顺序：

1. 通知相关人员短暂停用旧系统。
2. 停止旧服务器后端服务。
3. 重新执行旧数据库 `pg_dump`。
4. 重新同步附件目录。
5. 在新服务器 `pg_restore`。
6. 在新服务器执行 `alembic upgrade head`。
7. 启动新后端和前端。
8. 验收管理员、嘉宾、工作人员三端。
9. 确认无误后，让同事保留 `meeting.cssat.cn` 指向 `49.233.60.2`。

## 15. 日常更新

本地先检查：

```bash
cd /Users/wenguang/project/dm/green-mango
./scripts/check_all.sh
```

同步代码：

```bash
rsync -avz --delete \
  --exclude ".git" \
  --exclude "backend/.env" \
  --exclude "backend/.venv" \
  --exclude "backend/dev.db" \
  --exclude "frontend/node_modules" \
  --exclude "frontend/dist" \
  /Users/wenguang/project/dm/green-mango/ \
  tian@49.233.60.2:/opt/green-mango/app/
```

服务器备份当前代码和镜像：

```bash
sudo cp -a /opt/green-mango/app "/opt/green-mango/app.backup.$(date +%Y%m%d%H%M%S)"
docker image inspect zhihui-backend:latest >/dev/null 2>&1 && \
  docker tag zhihui-backend:latest "zhihui-backend:rollback-$(date +%Y%m%d%H%M%S)"
```

服务器更新：

```bash
cd /opt/green-mango/app/backend
docker build -t zhihui-backend:latest .
docker run --rm --network host \
  --env-file /opt/green-mango/shared/backend.env \
  zhihui-backend:latest alembic upgrade head
docker rm -f zhihui-api 2>/dev/null || true
docker run -d --name zhihui-api --restart unless-stopped \
  --network host \
  --env-file /opt/green-mango/shared/backend.env \
  zhihui-backend:latest \
  uvicorn app.main:app --host 127.0.0.1 --port 8010

cd /opt/green-mango/app/frontend
docker run --rm -v "$PWD":/app -w /app node:20-bookworm \
  bash -c "npm ci && npm run build"
```

Nginx 配置未变化时不需要 reload。

## 16. 常见问题

| 现象 | 处理方式 |
| --- | --- |
| `meeting.cssat.cn` 解析不到 IP | 等同事新增 DNS A 记录，或等待 DNS 生效 |
| Certbot 申请失败 | 检查 DNS 是否指向 `49.233.60.2`，安全组是否放行 80 |
| `/api/health` 返回 502 | 检查 `docker ps`、`docker logs zhihui-api --tail 100` |
| 数据库连接失败 | 检查 PostgreSQL 是否监听 `5432`、`pg_hba.conf` 是否允许密码认证、容器是否使用 `--network host` |
| 页面二维码还是旧域名 | 修改 `frontend/.env.production` 的 `VITE_PUBLIC_APP_URL` 后重新构建前端 |
| 附件下载失败 | 检查 `MATERIAL_STORAGE_DIR=/opt/green-mango/shared/materials`，确认旧附件已同步且权限正确 |
| 刷新子页面 404 | 检查 Nginx `location /` 是否包含 `try_files $uri $uri/ /index.html;` |
| 部署后其他网站异常 | 立即回滚本次公网入口变更，并恢复旧服务的原端口或原入口配置 |
| `8010` 端口已占用 | 改用 `8011` 等空闲端口，并同步修改后端启动端口和 Nginx `proxy_pass` |
| 容器名已存在 | 不要删除不属于本项目的容器；把本项目容器名改为 `green-mango-api` |

## 17. 安全要求

- 不把数据库密码、SSH Key、天气 Key、地图 Key 写入仓库。
- `/opt/green-mango/shared/backend.env` 权限保持 `600`。
- PostgreSQL 不对公网开放。
- 后端端口 `8010` 不对公网开放。
- 正式切换前更换测试账号密码。
- 迁移真实嘉宾数据前先确认备份和停机窗口。
