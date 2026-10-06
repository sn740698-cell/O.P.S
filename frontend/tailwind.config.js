/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Geist Mono"', '"Roboto Mono"', '"Space Mono"', 'monospace'],
        sans: ['Inter', '"Plus Jakarta Sans"', '"Work Sans"', '"Source Sans 3"', 'sans-serif'],
        heading: ['"Plus Jakarta Sans"', 'Outfit', 'Inter', 'sans-serif'],
        jakarta: ['"Plus Jakarta Sans"', 'sans-serif'],
        inter: ['Inter', 'sans-serif'],
        jetbrains: ['"JetBrains Mono"', 'monospace'],
        geist: ['"Geist Mono"', 'monospace'],
        outfit: ['Outfit', 'sans-serif'],
        worksans: ['"Work Sans"', 'sans-serif'],
        robotomono: ['"Roboto Mono"', 'monospace'],
        playfair: ['"Playfair Display"', 'serif'],
        sourcesans: ['"Source Sans 3"', 'sans-serif'],
        spacemono: ['"Space Mono"', 'monospace'],
      },
      colors: {
        ops: {
          bg: '#090d16',
          panel: '#111827',
          border: '#1f2937',
          accent: '#6366f1',
          success: '#10b981',
          warning: '#f59e0b',
        }
      },
    },
  },
  plugins: [],
}
