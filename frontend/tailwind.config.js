/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Geist Mono"', 'monospace'],
        sans: ['Geist', 'Inter', 'sans-serif'],
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
