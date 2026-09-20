import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The FastAPI backend serves the API and generated media on :8000.
const backend = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': backend, '/media': backend },
  },
})
