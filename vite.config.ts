import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

const certsDir = path.resolve(__dirname, 'certs')
const certsExist = fs.existsSync(path.join(certsDir, 'localhost-key.pem'))

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
  server: {
    port: 5173,
    ...(certsExist
      ? {
          https: {
            key: fs.readFileSync(path.join(certsDir, 'localhost-key.pem')),
            cert: fs.readFileSync(path.join(certsDir, 'localhost.pem')),
          },
        }
      : {}),
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
