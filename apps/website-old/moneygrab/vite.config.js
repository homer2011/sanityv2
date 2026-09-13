import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Deployed under https://sanityosrs.com/moneygrab/, so production builds use
// /moneygrab/ as the asset base. In dev we serve at the root and proxy /api
// and /auth to the live backend.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/moneygrab/' : '/',
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'https://sanityosrs.com',
        changeOrigin: true,
      },
      '/auth': {
        target: 'https://sanityosrs.com',
        changeOrigin: true,
      },
    },
  },
}))
