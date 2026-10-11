import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import { ANALYSIS } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { AnalysisScreen } from "./AnalysisScreen";

function start() {
  mockApi({ "GET /api/analysis": { body: ANALYSIS } });
  renderScreen(<AnalysisScreen />, { path: "/plans/:planId/analysis", url: "/plans/7/analysis" });
}

test("test_ac1_analysis_shows_median_and_suggested_amount", async () => {
  start();
  expect(
    await screen.findByRole("heading", { name: "Your spending analysis" }),
  ).toBeInTheDocument();
  expect(await screen.findByText("105,000 HUF")).toBeInTheDocument(); // heading renders before the data
  expect(screen.getByText("73,500 HUF")).toBeInTheDocument();
  expect(screen.getByText("70% of the median")).toBeInTheDocument();
  expect(screen.getByText(ANALYSIS.median_explanation ?? "")).toBeInTheDocument();
});

test("lists every month in an accessible table", async () => {
  start();
  const table = await screen.findByRole("table", { name: "Monthly surplus, last 6 months" });
  const rows = within(table).getAllByRole("row");
  expect(rows).toHaveLength(7); // header + 6 months
  expect(within(rows[6] ?? table).getByText("2026-09")).toBeInTheDocument();
  expect(within(rows[6] ?? table).getByText("300,000 HUF")).toBeInTheDocument();
});

test("continues to the plan", async () => {
  start();
  expect(await screen.findByRole("link", { name: "See my plan" })).toHaveAttribute(
    "href",
    "/plans/7",
  );
  expect(screen.getByText("Step 2 of 4")).toBeInTheDocument();
});
