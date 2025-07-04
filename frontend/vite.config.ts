import { defineConfig } from 'vite'
import tsConfigPaths from 'vite-tsconfig-paths'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import react from '@vitejs/plugin-react'


export default defineConfig({
  server: {
    port: 3000,
    allowedHosts: ['irradiations-pc'],
  },
  plugins: [
    tsConfigPaths({
      projects: ['./tsconfig.json'],
    }),
    tanstackRouter({ autoCodeSplitting: true }), 
    react()
  ],
})
