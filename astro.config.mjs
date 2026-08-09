
// import { defineConfig } from 'astro/config';
// import react from '@astrojs/react';
// import tailwindcss from '@tailwindcss/vite';

// export default defineConfig({
//   integrations: [react()],
//   vite: {
//     plugins: [tailwindcss()],
//   },
// });


// @ts-check
// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://dp1500.github.io',

  // GitHub Pages uses /quantmorning.
  // Local development uses /.
  base: import.meta.env.GITHUB_ACTIONS === 'true'
    ? '/quantmorning'
    : '',

  integrations: [react()],

  vite: {
    plugins: [tailwindcss()],
  },
});