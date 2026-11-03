/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        gc: {
          blue: {
            50: '#eaf1fb',
            100: '#d5e3f7',
            200: '#acc7ef',
            300: '#82abe7',
            400: '#427fd9',
            500: '#1d62c9',
            600: '#0e4ca7',
            700: '#053679', // Azul Oficial da Logo Global Cards
            800: '#042a5f',
            900: '#031e44',
            950: '#02132b',
          },
          orange: {
            50: '#fff7ed',
            100: '#ffedd5',
            200: '#fed7aa',
            300: '#fdba74',
            400: '#fb923c',
            500: '#f97316',
            600: '#ed6706', // Laranja Oficial da Logo Global Cards
            700: '#c24f04',
            800: '#9a3e05',
            900: '#7c3306',
          },
        },
        satiro: {
          50: '#eaf1fb',
          100: '#d5e3f7',
          200: '#acc7ef',
          500: '#053679',
          600: '#042a5f',
          700: '#053679',
          800: '#031e44',
          900: '#02132b',
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

