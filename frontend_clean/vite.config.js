import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import rollupNodePolyFill from 'rollup-plugin-node-polyfills';

export default defineConfig({
  plugins: [
    react(),
    rollupNodePolyFill() // fallback dacă ai nevoie de polyfill-uri
  ],
  optimizeDeps: {
    esbuildOptions: {
      define: {
        global: 'globalThis',
      },
    },
  },
  resolve: {
    alias: {
      buffer: 'buffer',
      stream: 'stream-browserify',
    },
  },
});
