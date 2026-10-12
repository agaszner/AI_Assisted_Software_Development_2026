import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const backend = fileURLToPath(new URL("../../backend", import.meta.url));

/**
 * Fresh demo data for every run: anna's plan from an earlier run would make signing a 409.
 * This WIPES the local development database.
 */
export default function globalSetup(): void {
  if (!process.env.SEED_PASSWORD) {
    throw new Error("SEED_PASSWORD is not set. Run `make e2e` (it loads .env).");
  }
  for (const args of [["migrate"], ["flush", "--no-input"], ["seed"]]) {
    execFileSync("uv", ["run", "python", "manage.py", ...args], { cwd: backend, stdio: "inherit" });
  }
}
