import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  root: "ui_components/",
  plugins: [svelte({
      compilerOptions: {
        customElement: true,
      },
    })],
  server: {
    cors: {
      origin: ["http://localhost:8000", "http://127.0.0.1:8000"]
    }
  },
  build: {
    manifest: "manifest.json",

    rollupOptions: {
      input: {
        main: "ui_components/src/main.ts",
      },
      output: {
        chunkFileNames: `[name].[hash].js`,
        entryFileNames: "[name].js",
        dir: "static/ui-components",
      },
    },
  },
})
