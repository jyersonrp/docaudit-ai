/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        zinc: {
          850: '#1e1e23',
          925: '#111114',
          950: '#09090b',
        },
        brand: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          500: '#06b6d4',
          600: '#0891b2',
          700: '#0e7490',
          900: '#164e63',
        }
      },
      boxShadow: {
        'glow-sm': '0 0 15px -3px rgba(14, 165, 233, 0.15)',
        'glow-md': '0 0 25px -5px rgba(14, 165, 233, 0.20)',
        'glow-rose': '0 0 20px -4px rgba(244, 63, 94, 0.20)',
        'glow-emerald': '0 0 20px -4px rgba(16, 185, 129, 0.20)',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
