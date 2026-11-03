/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        satiro: {
          50: '#f0f6fc',
          100: '#e0edf9',
          200: '#b9dbf3',
          500: '#0284c7',
          600: '#0369a1',
          700: '#0f3d6e',
          800: '#0b2d52',
          900: '#071e38',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
};

