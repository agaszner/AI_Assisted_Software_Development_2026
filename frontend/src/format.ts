/**
 * Display and input helpers. They format values from the API and parse customer input;
 * they never compute money or dates (golden rule 2).
 */
import type { Huf } from "./api/types";

const thousands = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export const AMOUNT_HINT = "Whole forints. Cannot be negative.";

/** 1220000 → "1,220,000". */
export function formatNumber(amount: Huf): string {
  return thousands.format(amount);
}

/** 73500 → "73,500 HUF", the same format as the backend explanation templates. */
export function formatHuf(amount: Huf): string {
  return `${formatNumber(amount)} HUF`;
}

/** Transaction amounts on Home: "+550,000 HUF", "−150,000 HUF" (typographic minus, Figma 02). */
export function formatSigned(amount: Huf): string {
  if (amount > 0) return `+${formatHuf(amount)}`;
  if (amount < 0) return `−${formatNumber(Math.abs(amount))} HUF`;
  return formatHuf(amount);
}

/** "2026-09-01" → "2026-09". String slicing, so no time-zone shift. */
export function formatMonth(iso: string): string {
  return iso.slice(0, 7);
}

/** "2026-10-06T10:00:00Z" → "2026-10-06". */
export function formatDay(iso: string): string {
  return iso.slice(0, 10);
}

/** "2025-12-01" → "Dec" (chart axis). */
export function monthName(iso: string): string {
  return MONTHS[Number(iso.slice(5, 7)) - 1] ?? iso.slice(5, 7);
}

/** "2025-12-01" → "2025". */
export function monthYear(iso: string): string {
  return iso.slice(0, 4);
}

/** "anna" → "Anna" (greeting and sidebar). */
export function displayName(username: string): string {
  return username.charAt(0).toUpperCase() + username.slice(1);
}

/**
 * A whole, non-negative forint amount typed by the customer. Spaces and thousands commas are
 * allowed ("250 000", "250,000"). Decimals, signs, exponents and empty text give null.
 */
export function parseHuf(text: string): Huf | null {
  const digits = text.replace(/[\s,]/g, "");
  if (!/^\d+$/.test(digits)) return null;
  const value = Number(digits);
  return Number.isSafeInteger(value) ? value : null;
}
