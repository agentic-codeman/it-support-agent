import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  root: '.',  // 明确指定根目录
  server: {
    port: 5173,
    host: true,  // 使用true而不是'0.0.0.0'，Vite会自动处理
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
