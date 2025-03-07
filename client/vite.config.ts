import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Add static file serving for shared directory
    static: {
      directory: path.resolve(__dirname, '../shared'),
      prefix: '/shared/',
    },
  },
})
