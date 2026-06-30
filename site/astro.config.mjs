// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';

// Канон URL: домен + trailing-slash + directory-формат → /cao/zamoskvoreche/index.html
// (1:1 с текущим website/vercel.json trailingSlash:true → катовер без 301).
// https://astro.build/config
export default defineConfig({
  site: 'https://beloliptsev.ru',
  output: 'static',
  trailingSlash: 'always',
  build: {
    format: 'directory',
  },
  integrations: [
    sitemap(),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
