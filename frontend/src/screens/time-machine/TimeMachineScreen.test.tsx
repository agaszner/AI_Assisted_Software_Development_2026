import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import { MACHINE, PLAN, plan } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { TimeMachineScreen } from "./TimeMachineScreen";

const NOTE = MACHINE.months[2]?.note ?? "";

function start(current = PLAN) {
  mockApi({
    "GET /api/plans/7": { body: current },
    "GET /api/plans/7/time-machine": { body: MACHINE },
  });
  renderScreen(<TimeMachineScreen />, {
    path: "/plans/:planId/time-machine",
    url: "/plans/7/time-machine",
  });
}

test("test_ac4_time_machine_flags_skipped_month", async () => {
  start();
  const table = await screen.findByRole("table", { name: "Saved to date, month by month" });
  const skippedRow = within(table).getByRole("row", { name: /2025-12/ });
  expect(within(skippedRow).getByText("Skipped")).toBeInTheDocument();
  expect(within(skippedRow).getByText("147,000 HUF")).toBeInTheDocument(); // total unchanged
  const list = screen.getByRole("list", { name: "Skipped months" });
  expect(within(list).getByText(NOTE)).toBeInTheDocument();
});

test("test_ac4_time_machine_shows_totals_from_the_api", async () => {
  start();
  const tiles = await screen.findByRole("region", { name: "Totals" });
  expect(within(tiles).getByText("147,000 HUF")).toBeInTheDocument();
  expect(within(tiles).getByText("2 of 3")).toBeInTheDocument();
  expect(within(tiles).getByText(/a month when it ran/)).toBeInTheDocument();
  expect(
    screen.getByText("past behaviour only, not a forecast.", { exact: false }),
  ).toBeInTheDocument();
});

test("continues to the mandate only for a proposed plan", async () => {
  start();
  expect(await screen.findByRole("link", { name: "Continue to mandate" })).toHaveAttribute(
    "href",
    "/plans/7/mandate",
  );
});

test("an accepted plan shows the replay without signing", async () => {
  start(plan({ status: "accepted" }));
  await screen.findByRole("table", { name: "Saved to date, month by month" });
  expect(screen.queryByRole("link", { name: "Continue to mandate" })).toBeNull();
});
