import type { Config } from "tailwindcss";

const config: Config = {
  theme: {
    extend: {
      colors: {
        forest: "#1f4d3a",
        "forest-light": "#c8e6d3",
        surface: "#f6f8f7",
        ink: "#0d1f17",
        "ink-soft": "#4a5852",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          '"Liberation Mono"',
          '"Courier New"',
          "monospace",
        ],
      },
    },
  },
};

export default config;
