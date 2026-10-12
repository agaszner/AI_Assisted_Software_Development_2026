import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { PlanOut } from "../../api/types";
import { plan } from "../../test/fixtures";
import { mockApi, renderScreen, type Handler } from "../../test/render";
import { ActivePlanScreen } from "./ActivePlanScreen";

const ACTIVE = plan({ status: "accepted", mandate_version: 1, signed_on: "2026-10-08" });

function start(active: PlanOut | null = ACTIVE, routes: Record<string, Handler> = {}) {
  const calls = mockApi({
    "GET /api/plans/active":
      active === null ? { status: 404, body: { detail: "No active plan." } } : { body: active },
    "GET /api/activity": { body: [] },
    ...routes,
  });
  renderScreen(<ActivePlanScreen />, { path: "/plan" });
  return { calls, user: userEvent.setup() };
}

test("shows the plan facts and recurring orders from the API", async () => {
  start();
  expect(
    await screen.findByText("Accepted 2026-10-08 under mandate version 1."),
  ).toBeInTheDocument();
  expect(screen.getByText("Version 1")).toBeInTheDocument();
  expect(screen.getByText("3 recurring orders")).toBeInTheDocument();
  const orders = screen.getByRole("list", { name: "Recurring orders" });
  expect(within(orders).getAllByRole("listitem")).toHaveLength(3);
  expect(
    within(orders).getByText("Short government bond fund · until 2027-08-01"),
  ).toBeInTheDocument();
});

test("shows the empty state when there is no active plan", async () => {
  start(null);
  expect(await screen.findByRole("link", { name: "Start a savings plan" })).toHaveAttribute(
    "href",
    "/questionnaire",
  );
});

test("pause asks for confirmation, then pauses", async () => {
  const { calls, user } = start(ACTIVE, {
    "POST /api/plans/7/pause": { body: plan({ status: "paused" }) },
  });
  await user.click(await screen.findByRole("button", { name: "Pause plan" }));
  const dialog = screen.getByRole("dialog", { name: "Pause your savings plan?" });
  await user.click(within(dialog).getByRole("button", { name: "Pause plan" }));
  expect(calls.filter((c) => c.method === "POST").map((c) => c.path)).toEqual([
    "/api/plans/7/pause",
  ]);
});

test("change amount proposes a revision and opens its review", async () => {
  const { calls, user } = start(ACTIVE, {
    "POST /api/plans/7/revise": { body: plan({ id: 12, revises: 7, monthly_amount: 50_000 }) },
  });
  await user.click(await screen.findByRole("button", { name: "Change amount" }));
  const dialog = screen.getByRole("dialog", { name: "Change the monthly amount" });
  await user.clear(within(dialog).getByLabelText("New monthly amount"));
  await user.type(within(dialog).getByLabelText("New monthly amount"), "50000");
  await user.click(within(dialog).getByRole("button", { name: "Propose new amount" }));
  expect(await screen.findByText("Navigated to /plans/12")).toBeInTheDocument();
  expect(calls.find((c) => c.method === "POST")?.body).toEqual({ monthly_amount: 50_000 });
});

test("a revision error is shown in the change-amount modal", async () => {
  const { user } = start(ACTIVE, {
    "POST /api/plans/7/revise": {
      status: 409,
      body: { detail: "A revised plan is already waiting for your signature." },
    },
  });
  await user.click(await screen.findByRole("button", { name: "Change amount" }));
  const dialog = screen.getByRole("dialog", { name: "Change the monthly amount" });
  await user.click(within(dialog).getByRole("button", { name: "Propose new amount" }));
  expect(await within(dialog).findByRole("alert")).toHaveTextContent(
    "A revised plan is already waiting for your signature.",
  );
});

test("a pending revision links to its review", async () => {
  start(plan({ ...ACTIVE, pending_revision: 12 }));
  expect(await screen.findByRole("link", { name: "Review the new amount" })).toHaveAttribute(
    "href",
    "/plans/12",
  );
});

test("a paused plan offers no pause or change", async () => {
  start(plan({ ...ACTIVE, status: "paused" }));
  await screen.findByText("Paused");
  expect(screen.queryByRole("button", { name: "Pause plan" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Change amount" })).toBeNull();
});
