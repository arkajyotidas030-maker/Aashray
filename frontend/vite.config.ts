import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "AASHRAY",
        short_name: "AASHRAY",
        description: "Disaster situation awareness",
        theme_color: "#134e4a",
        background_color: "#f7f3eb",
        display: "standalone",
        start_url: "/",
      },
    }),
  ],
  server: { port: 5173 },
});
