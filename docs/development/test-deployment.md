# 测试环境部署

本文记录 `cssat.wenguang.top` 的嘉宾端演示环境部署边界。测试环境用于内部演示，不承载真实嘉宾数据。

## 部署结构

```text
浏览器 -> Nginx :443 -> Vue 静态资源
                    -> /api -> FastAPI 127.0.0.1:8010 -> SQLite
```

- 应用目录：`/opt/zhihui-demo/app`
- 运行时配置：`/opt/zhihui-demo/shared/backend.env`
- 后端服务：`zhihui-demo.service`
- Nginx 配置：`/etc/nginx/conf.d/cssat.wenguang.top.conf`
- TLS（传输层安全协议）证书：Let's Encrypt，由 Certbot 续期

## 环境边界

- 前端构建时使用同源 `/api`，公开会议入口使用 `https://cssat.wenguang.top`。
- 后端只监听服务器本机 `127.0.0.1:8010`，公网请求统一经过 Nginx。
- 数据库使用独立 SQLite 文件，不连接本地开发数据库或正式数据库。
- 通用本地联调数据由 `python -m app.scripts.seed_dev` 创建；公网领导演示数据由 `python -m app.scripts.seed_demo` 创建，严禁录入真实个人信息。
- 天气和地点搜索需要单独配置第三方服务凭据；未配置时使用现有中文降级提示。

## 更新与验证

每次更新应先运行：

```bash
./scripts/check_all.sh
cd frontend && npm run build
```

部署后至少验证健康检查、会议入口、嘉宾登录、嘉宾首页和前端子路由刷新。修改 Nginx 前必须先执行 `nginx -t`，修改后端后必须确认 `zhihui-demo.service` 为运行状态。

## 安全要求

- 不在仓库中保存服务器密码、SSH Key、数据库密钥或第三方服务凭据。
- 测试服务器优先使用 SSH Key 登录并关闭 root 密码远程登录。
- 测试账号仅用于内部演示，正式试用前必须更换。
