/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Vert agricole — identité TerraLink.
        terra: {
          600: "#16a34a",
          700: "#15803d",
          800: "#166534",
        },
      },
    },
  },
  plugins: [],
};
