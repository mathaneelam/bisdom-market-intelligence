/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0f4ff",
          100: "#dde8ff",
          500: "#3b6bff",
          600: "#2a57f5",
          700: "#1d45d4",
        },
      },
    },
  },
  plugins: [],
};
