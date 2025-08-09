/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html", 
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Exact RGB values from homepage-new
        "bg-primary": "rgb(17, 17, 16)",
        "text-primary": "rgb(255, 255, 255)",
        "text-secondary": "rgb(181, 179, 173)",
        "text-accent": "rgb(238, 238, 236)",
        "border-default": "rgb(55, 55, 53)",
        "border-hover": "rgb(100, 100, 98)",
        "hover-bg": "rgb(26, 26, 24)",
        // Spotify green accent
        "spotify": "#39FF14",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "system-ui",
          "sans-serif",
        ],
      },
      letterSpacing: {
        "0.02em": "0.02em",
        "0.03em": "0.03em",
      },
      lineHeight: {
        "16px": "16px",
        "26.4px": "26.4px",
      },
      transitionDuration: {
        "20ms": "20ms",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "bounce-smooth": "bounce-smooth 2s ease-in-out 2",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "bounce-smooth": {
          "0%, 20%, 50%, 80%, 100%": { transform: "translateY(0px)" },
          "40%": { transform: "translateY(-8px)" },
          "60%": { transform: "translateY(-4px)" },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}