import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "vitest";

// Vitest runs from frontend/ (jsdom gives import.meta.url an http scheme, so no URL here).
const SRC = join(process.cwd(), "src");
// Hex colours or Tailwind arbitrary values ("p-[13px]") bypass the Figma tokens.
const RAW_STYLE = /#[0-9a-fA-F]{3,8}\b|\b[\w:-]+-\[[^\]]+\]/;
// "Today" comes from the API (SAVERAI_FIXED_DATE); the client clock must not decide anything.
const CLIENT_CLOCK = /new Date\(|Date\.now\(/;

function appFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return entry.name === "test" ? [] : appFiles(path);
    return /\.tsx?$/.test(entry.name) && !entry.name.includes(".test.") ? [path] : [];
  });
}

test("app code uses only theme tokens", () => {
  const offenders = appFiles(SRC).filter((file) => RAW_STYLE.test(readFileSync(file, "utf8")));
  expect(offenders).toEqual([]);
});

test("app code never reads the client clock", () => {
  const offenders = appFiles(SRC).filter((file) => CLIENT_CLOCK.test(readFileSync(file, "utf8")));
  expect(offenders).toEqual([]);
});
