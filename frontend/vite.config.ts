// @ts-ignore - process is available in Node.js context
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// @ts-ignore - process is Node.js global in config files
const apiBase = process.env.VITE_API_BASE || '';

export default defineConfig({
  plugins: [react()],
  define: {
    // Inject environment variable into JavaScript at build time
    __VITE_API_BASE__: JSON.stringify(apiBase),
  },
  server: {
    proxy: {
      '/run': 'http://localhost:8000',
      '/status': 'http://localhost:8000',
      '/report': 'http://localhost:8000',
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/screenshots': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
  },
});
