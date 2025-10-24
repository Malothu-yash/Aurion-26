import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { cloudflare } from "@cloudflare/vite-plugin";
import { mochaPlugins } from "@getmocha/vite-plugins";

const enableCloudflare =
  process.env.VITE_ENABLE_CLOUDFLARE === '1' ||
  process.env.CF_PAGES === '1' ||
  process.env.CI === 'true';

export default defineConfig({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  plugins: [
    ...mochaPlugins(process.env as any),
    react(),
    ...(enableCloudflare ? [cloudflare()] : [])
  ],
  server: {
    allowedHosts: true,
    hmr: {
      overlay: false,
    },
    port: 5173,
    host: true,
  },
  build: {
    chunkSizeWarningLimit: 5000,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['lucide-react']
        }
      }
    },
    sourcemap: false
  },
  esbuild: {
    drop: ['console', 'debugger']
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
