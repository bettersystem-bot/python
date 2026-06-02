import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 开发时把 /api、/internal、/ws 代理到后端 core service，避免跨域与硬编码地址。
// 后端地址可用环境变量 VITE_BACKEND 覆盖（docker-compose 里指向 backend 服务名）。
const backend = process.env.VITE_BACKEND || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': { target: backend, changeOrigin: true },
      '/internal': { target: backend, changeOrigin: true },
      '/ws': { target: backend, ws: true, changeOrigin: true },
    },
  },
})
