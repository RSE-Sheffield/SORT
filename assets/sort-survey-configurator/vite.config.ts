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
        sort_survey_config: "./src/main.ts",
        sort_survey_cd: "./src/survey_config_consent_demography.ts",
        sort_survey_response: "./src/survey_response.ts"
      },
      // single
      output: {
        // format: "umd",
        chunkFileNames: `[name].[hash].js`,
        entryFileNames: "[name].js",
        dir: "../../static/js/sort-ui",
      },
    },
  },
})
