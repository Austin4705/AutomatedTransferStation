import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Listen on all network interfaces (allows both localhost and 127.0.0.1)
    port: 5173,
    // Add static file serving for shared directory
    static: {
      directory: path.resolve(__dirname, '../shared'),
      prefix: '/shared/',
    },
  },
})
