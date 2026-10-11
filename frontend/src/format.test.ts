import { describe, expect, test } from "vitest";
import {
  displayName,
  formatCompact,
  formatDay,
  formatHuf,
  formatMonth,
  formatNumber,
  formatSigned,
  monthName,
  monthYear,
  parseHuf,
} from "./format";

test("formatHuf matches the backend explanation format", () => {
  expect(formatHuf(73_500)).toBe("73,500 HUF");
  expect(formatHuf(-40_000)).toBe("-40,000 HUF");
  expect(formatHuf(0)).toBe("0 HUF");
  expect(formatNumber(1_220_000)).toBe("1,220,000");
});

test("formatSigned marks income and expenses like Figma 02", () => {
  expect(formatSigned(550_000)).toBe("+550,000 HUF");
  expect(formatSigned(-150_000)).toBe("−150,000 HUF");
});

test("dates are sliced, never shifted by time zone", () => {
  expect(formatMonth("2026-09-01")).toBe("2026-09");
  expect(formatDay("2026-10-06T23:30:00Z")).toBe("2026-10-06");
  expect(monthName("2025-12-01")).toBe("Dec");
  expect(monthYear("2025-12-01")).toBe("2025");
});

test("displayName capitalises the username", () => {
  expect(displayName("anna")).toBe("Anna");
});

describe("parseHuf", () => {
  test.each([
    ["250000", 250_000],
    ["250 000", 250_000],
    ["250,000", 250_000],
    [" 0 ", 0],
  ])("accepts %j", (text, expected) => {
    expect(parseHuf(text)).toBe(expected);
  });

  test.each([
    "",
    "   ",
    "-5",
    "-50,000",
    "100.5",
    "100.0",
    "1e5",
    "abc",
    "12a",
    "99999999999999999999",
  ])("rejects %j", (text) => {
    expect(parseHuf(text)).toBeNull();
  });
});

test("formatCompact labels chart axes", () => {
  expect(formatCompact(100_000)).toBe("100k");
  expect(formatCompact(750_000)).toBe("750k");
  expect(formatCompact(0)).toBe("0");
});
