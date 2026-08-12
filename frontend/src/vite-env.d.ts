/// <reference types="vite/client" />

/**
 * 前端构建环境变量类型声明。
 *
 * 新增 Vite 环境变量后需同步补充声明，避免 `import.meta.env` 类型缺失。
 */
interface ImportMetaEnv {
  /** 根路径默认进入的公开会议 ID；留空时根路径回退到管理员登录页。 */
  readonly VITE_PUBLIC_DEFAULT_MEETING_ID?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
