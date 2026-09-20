import fs from "node:fs";
import path from "node:path";
import { defineConfig, devices } from "@playwright/test";
import { fileURLToPath } from "node:url";

const frontendRoot = path.dirname(fileURLToPath(import.meta.url));
const backendRoot = path.join(frontendRoot, "..", "backend");
const win = process.platform === "win32";
const py = path.join(backendRoot, ".venv", win ? "Scripts/python.exe" : "bin/python");
const python = fs.existsSync(py) ? py : "python";

export default defineConfig({
  testDir: "./e2e",
  timeout: 180_000,
  fullyParallel: false,
  retries: 0,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:5174",
    headless: true,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `"${python}" scripts/e2e_api.py`,
      cwd: backendRoot,
      url: "http://127.0.0.1:8010/api/v1/health",
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ...process.env,
        DATABASE_URL: "sqlite:///./e2e_playwright.db",
        JWT_SECRET: "playwright-secret-must-be-32-chars",
        DEMO_MODE: "1",
        LLM_API_KEY: "",
        OSRM_URL: "",
        SEED_PASSWORD: "demo",
        CORS_ORIGINS: "http://127.0.0.1:5174,http://localhost:5174",
      },
    },
    {
      command: "npx vite --host 127.0.0.1 --port 5174",
      cwd: frontendRoot,
      url: "http://127.0.0.1:5174",
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        ...process.env,
        VITE_API_BASE_URL: "http://127.0.0.1:8010",
      },
    },
  ],
});
