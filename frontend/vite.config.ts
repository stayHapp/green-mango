import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // 开发服务监听全部网卡，便于同一局域网内的手机访问嘉宾端。
  server: {
    host: '0.0.0.0',
    // 本地开发统一使用同源 /api，避免手机把 127.0.0.1 解释为手机自身。
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
