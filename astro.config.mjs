// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://dp1500.github.io',

  integrations: [react()],

  vite: {
    plugins: [tailwindcss()],
  },
});