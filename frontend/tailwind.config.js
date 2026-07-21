/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#C9A84C",
        background: "#121212",
        surface: "#1E1E1E",
        textPrimary: "#FFFFFF",
        textSecondary: "#A0A0A0",
      },
      fontFamily: {
        sans: ['"Noto Sans KR"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
