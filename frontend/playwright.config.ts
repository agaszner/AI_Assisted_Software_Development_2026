import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  workers: 1, // one shared SQLite database
  use: {
    ...devices["Desktop Chrome"],
    viewport: { width: 1440, height: 900 }, // Figma desktop frames
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  // Reuses `make dev` servers when they run; starts them otherwise.
  webServer: [
    {
      command: "cd ../backend && uv run python manage.py runserver 8000",
      url: "http://localhost:8000/api/docs",
      reuseExistingServer: true,
    },
    { command: "npm run dev", url: "http://localhost:5173", reuseExistingServer: true },
  ],
});
