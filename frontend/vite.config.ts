/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    // Dev proxy: the browser calls /api on the Vite server, Vite forwards it to Django.
    // Same idea as Angular's proxy.conf.json, and it avoids CORS in dev.
    proxy: {
      '/api': { target: process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    // MUI is most of the main bundle; fine for a LAN app. Charts are split out (lazy Stats page).
    chunkSizeWarningLimit: 800,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    // Node's fetch needs absolute URLs; MSW intercepts this host. Never a real backend.
    env: { VITE_API_URL: 'http://api.test/api/v1' },
  },
});
