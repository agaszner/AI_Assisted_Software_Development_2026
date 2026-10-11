import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

beforeEach(() => {
  document.cookie = "csrftoken=test-token";
});

// Recharts' ResponsiveContainer needs ResizeObserver, which jsdom lacks. Charts render at zero
// size in tests, so assertions use the month tables, not the SVG.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
globalThis.ResizeObserver = ResizeObserverStub;
