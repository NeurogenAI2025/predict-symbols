kimport { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ['@solana/web3.js'], // 👉 spune Vite să preproceseze acest modul
  },
  build: {
    rollupOptions: {
      external: ['@solana/web3.js'], // 👉 împiedică Rollup să încerce să-l rezolve din nou
    },
  },
});

