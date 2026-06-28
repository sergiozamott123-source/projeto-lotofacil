/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        lotofacil: {
          purple: '#7B2D8B',
          green: '#00A651',
          yellow: '#FFF200',
        },
      },
    },
  },
  plugins: [],
}
