/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

// The dashboard lives in <academy>/dashboard and imports the Markdown dossier
// from the academy root at build time (see src/content/load.ts). The dev server
// must therefore be allowed to read one level up.
const academyRoot = fileURLToPath(new URL('..', import.meta.url))

export default defineConfig({
  plugins: [react()],
  base: './', // relative asset paths: dist/ can be served from any folder
  server: {
    port: 5173,
    fs: { allow: [academyRoot] },
  },
  preview: { port: 4173 },
  build: {
    chunkSizeWarningLimit: 1500, // mermaid is large; it is lazy-loaded
  },
  test: {
    environment: 'node',
    include: ['src/test/**/*.test.ts'],
  },
})
