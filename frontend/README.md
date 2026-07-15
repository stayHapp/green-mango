# Frontend

知会前端项目，使用 Vue 3、Vite 和 TypeScript 实现管理员端、嘉宾端、工作人员端。登录和退出已开始接入真实 FastAPI 会话，其余业务页面按联调计划逐步从 Mock 切换。

计划技术栈：

- Vue 3
- Vite
- TypeScript
- Element Plus
- Vue Router
- Pinia
- Axios

## 启动开发服务

在本目录运行：

```bash
npm install
npm run dev
```

启动成功后，按终端输出的本地地址在浏览器中访问。首次运行或 `package.json`、`package-lock.json` 变更后，需要先执行 `npm install`。

默认请求 `http://127.0.0.1:8000/api`。需要修改后端地址时，从 `.env.example` 创建 `.env.local`：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_PUBLIC_APP_URL=http://192.168.1.100:5173
```

`VITE_PUBLIC_APP_URL` 用于管理员端生成会议入口链接和二维码。本地联调应填写本机局域网 IP，正式环境应填写嘉宾能够访问的域名，不能填写 `localhost`。

三端本地演示账号由后端 `python -m app.scripts.seed_dev` 命令创建，具体凭据见后端 README。

## 可用命令

```bash
npm run dev      # 启动开发服务
npm run build    # 执行类型检查并构建生产产物
npm run preview  # 本地预览生产构建产物
```
