/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f6ff',
          100: '#e0edfe',
          200: '#bae0fd',
          500: '#0064d2',
          600: '#0054b3',
          700: '#00438f',
          900: '#002657',
        },
      },
    },
  },
  plugins: [],
}
