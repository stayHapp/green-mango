# 本地手动启动

本文说明如何在开发电脑上手动启动知会前后端，并允许同一局域网内的手机访问。

## 前置条件

- Python 3.12 和后端 `.venv` 已准备完成。
- Node.js 和前端依赖已安装。
- `backend/.env` 已按需配置数据库、和风天气及高德服务。
- `frontend/.env.local` 中 `VITE_API_BASE_URL=/api`。
- 手机与电脑连接同一个 Wi-Fi 或局域网。

## 第一步：启动后端

打开第一个终端窗口，在仓库根目录执行：

```bash
cd backend
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

看到以下信息表示后端启动成功：

```text
Uvicorn running on http://0.0.0.0:8000
```

可在电脑浏览器检查：

```text
http://127.0.0.1:8000/api/health
```

## 第二步：启动前端

保持后端终端运行，再打开第二个终端窗口，在仓库根目录执行：

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

Vite 会输出类似地址：

```text
Local:   http://localhost:5173/
Network: http://192.168.10.171:5173/
```

电脑可以访问：

```text
http://127.0.0.1:5173/
```

手机应访问 Vite 输出的 `Network` 地址，不能访问 `localhost` 或 `127.0.0.1`。

## API 转发方式

前端开发环境统一请求同源 `/api`。Vite 将请求代理到电脑上的：

```text
http://127.0.0.1:8000
```

因此电脑和手机都只需要访问前端的 `5173` 端口，手机不会错误请求自身的 `127.0.0.1`。

## 查看电脑局域网 IP

macOS 可以运行：

```bash
ipconfig getifaddr en0
```

如果没有输出，可以执行：

```bash
ifconfig | grep "inet "
```

IP 变化后，应同步修改 `frontend/.env.local` 中的：

```text
VITE_PUBLIC_APP_URL=http://当前局域网IP:5173
```

修改 `.env.local` 或 `vite.config.ts` 后必须重启前端服务。

## 停止服务

分别回到前端和后端终端，按：

```text
Control + C
```

不要直接关闭正在执行数据库迁移的终端。

## 常见问题

### 页面完全打不开

检查端口是否监听：

```bash
lsof -nP -iTCP:5173 -sTCP:LISTEN
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

### 页面提示无法连接后端

确认后端健康接口正常：

```bash
curl http://127.0.0.1:8000/api/health
```

并确认 `frontend/.env.local` 使用：

```text
VITE_API_BASE_URL=/api
```

### 电脑可以访问但手机不行

- 确认手机与电脑连接同一网络。
- 使用 Vite 输出的 `Network` 地址。
- 确认前端使用 `--host 0.0.0.0` 启动。
- 检查 macOS 防火墙是否阻止 Node.js 接收入站连接。
- 公司、校园或访客 Wi-Fi 可能开启设备隔离，此时可改用个人热点测试。
