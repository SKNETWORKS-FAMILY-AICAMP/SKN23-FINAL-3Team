import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  publicDir: 'assets',
  envDir: '../',  // 루트 .env 파일 사용
  server: {
    host: true,        // 같은 Wi-Fi 다른 노트북에서 접속 허용 (0.0.0.0 바인딩)
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
