import { defineConfig } from 'vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  resolve: {
    tsconfigPaths: true,
  },
  server: {
    port: 3000,
    allowedHosts: ['irradiations-pc', 'orbitos-demo.izzecloud.duckdns.org'],
  },
  plugins: [
    tanstackRouter({ autoCodeSplitting: true }),
    react(),
  ],
})
