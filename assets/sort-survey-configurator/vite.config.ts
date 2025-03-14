import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte({
      compilerOptions: {
        customElement: true,
      },
    })],
  server: {
    cors: {
      origin: "http://localhost:8000"
    }
  },
  build: {
    manifest: true,

    rollupOptions: {
      input: {
        sort_survey_config: "./src/main.ts",
        sort_survey_cd: "./src/survey_config_consent_demography.ts",
        sort_survey_response: "./src/survey_response.ts"
      },
      output: {
        chunkFileNames: `[name].[hash].js`,
        entryFileNames: "[name].js",
        dir: "../../static/sort-ui",
      },
    },
  },
})
