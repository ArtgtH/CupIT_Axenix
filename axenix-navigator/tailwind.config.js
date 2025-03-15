/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#f2581c',
        secondary: '#181311',
        tertiary: '#8a6c60',
        border: '#f5f1f0',
      },
    },
  },
  plugins: [],
} 