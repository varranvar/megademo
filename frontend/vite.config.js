import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [
    svelte({
      compilerOptions: {
        runes: true
      }
    })
  ],
  resolve: {
    conditions: ['browser', 'sass'],
  },
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: ['import', 'global-builtin', 'legacy-js-api'],
      }
    }
  },
  build: {
    ssr: false
  },
  server: {
    port: 5173,
    open: true
  },
  publicDir: 'data'
})
