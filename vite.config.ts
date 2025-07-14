import {defineConfig} from 'vitest/config'
import {svelte} from '@sveltejs/vite-plugin-svelte'

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
                main: "./ui_components/src/main.ts",
            },
            output: {
                chunkFileNames: `[name].[hash].js`,
                entryFileNames: "[name].js",
                dir: "./static/ui-components",
            },
        },
    },
    test: {
        // Svelte component testing
        // https://svelte.dev/docs/svelte/testing
        // DOM environment for client-side component testing
        environment: "jsdom",
        setupFiles: ['./tests/test-setup.js'],
        globals: true,
        coverage: {
            provider: "v8",
            reporter: ["text", "json", "json-summary"]
        },
    },
    // Tell Vitest to use the `browser` entry points in `package.json` files, even though it's running in Node
    resolve: process.env.VITEST ? {conditions: ["browser"]} : undefined,
})
