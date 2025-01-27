import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte({
      compilerOptions: {
        customElement: true,
      },
    })],
  build: {
    target: "esnext",
    rollupOptions: {
      input: {
        index: "./src/main.ts",
      },
      // single
      output: {
        format: "umd",
        chunkFileNames: `[name].[hash].js`,
        entryFileNames: "[name].umd.js", // <--
        dir: "dist",
      },
    },
  },
})
