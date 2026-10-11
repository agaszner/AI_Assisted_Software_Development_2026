import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import { MACHINE, PLAN, plan } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { TimeMachineScreen } from "./TimeMachineScreen";

function start(status: "proposed" | "accepted" = "proposed") {
  mockApi({
    "GET /api/plans/7": { body: plan({ status }) },
    "GET /api/plans/7/time-machine": { body: MACHINE },
  });
  renderScreen(<TimeMachineScreen />, {
    path: "/plans/:planId/time-machine",
    url: "/plans/7/time-machine",
  });
}

test("test_ac4_time_machine_screen_flags_skipped_month_with_backend_note", async () => {
  start();
  expect(await screen.findByText("Saved over 3 months")).toBeInTheDocument();
  expect(screen.getByText("2 of 3")).toBeInTheDocument();
  const skipped = screen.getByRole("heading", { name: /Skipped months/ }).closest("section");
  expect(
    within(skipped as HTMLElement).getByText(MACHINE.months[2]?.note ?? ""),
  ).toBeInTheDocument();
  expect(screen.getByRole("row", { name: /2025-12/ })).toHaveTextContent("Skipped");
  expect(
    screen.getByText(`${PLAN.monthly_amount.toLocaleString("en-US")} HUF a month when it ran`),
  ).toBeInTheDocument();
});

test("continue to mandate only for proposed plans", async () => {
  start();
  expect(await screen.findByRole("link", { name: "Continue to mandate" })).toHaveAttribute(
    "href",
    "/plans/7/mandate",
  );
});

test("no continue link once the plan is accepted", async () => {
  start("accepted");
  await screen.findByText("Saved over 3 months");
  expect(screen.queryByRole("link", { name: "Continue to mandate" })).toBeNull();
});
