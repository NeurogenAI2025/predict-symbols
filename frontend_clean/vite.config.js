import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: ["@solana/web3.js"],
  },
  resolve: {
    alias: {
      "@solana/web3.js": "node_modules/@solana/web3.js",
    },
  },
});
