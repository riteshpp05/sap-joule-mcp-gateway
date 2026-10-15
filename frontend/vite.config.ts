import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static_react',
    emptyOutDir: true,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://127.0.0.1:8080',
      '/health': 'http://127.0.0.1:8080',
      '/metrics': 'http://127.0.0.1:8080',
      '/docs': 'http://127.0.0.1:8080',
      '/openapi.json': 'http://127.0.0.1:8080',
      '/mcp': 'http://127.0.0.1:8080',
      '/sse': 'http://127.0.0.1:8080',
    },
  },
});
