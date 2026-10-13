import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/score': 'http://127.0.0.1:8000',
      '/compare': 'http://127.0.0.1:8000',
      '/arena': 'http://127.0.0.1:8000',
      '/leaderboard': 'http://127.0.0.1:8000',
      '/validation': 'http://127.0.0.1:8000',
      '/ready': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    }
  }
})
