import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { PlanOut } from "../../api/types";
import { LOW_CONFIDENCE_PLAN, MACHINE, PLAN, plan } from "../../test/fixtures";
import { mockApi, renderScreen, type Handler } from "../../test/render";
import { PlanReviewScreen } from "./PlanReviewScreen";

function start(current: PlanOut = PLAN, routes: Record<string, Handler> = {}) {
  const calls = mockApi({
    [`GET /api/plans/${current.id}`]: { body: current },
    [`GET /api/plans/${current.id}/time-machine`]: { body: MACHINE },
    ...routes,
  });
  renderScreen(<PlanReviewScreen />, { path: "/plans/:planId", url: `/plans/${current.id}` });
  return { calls, user: userEvent.setup() };
}

test("test_ac1_plan_review_shows_73500_with_high_confidence", async () => {
  start();
  const panel = await screen.findByRole("complementary", { name: "Summary" });
  expect(within(panel).getByText("73,500 HUF")).toBeInTheDocument();
  expect(within(panel).getByText("High confidence")).toBeInTheDocument();
  expect(screen.getByText(PLAN.explanations[0] ?? "")).toBeInTheDocument();
  expect(within(panel).getByRole("link", { name: "Continue to mandate" })).toHaveAttribute(
    "href",
    "/plans/7/mandate",
  );
});

test("test_ac2_emergency_fund_is_the_first_item", async () => {
  start();
  const list = await screen.findByRole("list", { name: "Plan items" });
  const [first] = within(list).getAllByRole("listitem");
  expect(first).toHaveTextContent("Emergency fund");
  expect(first).toHaveTextContent("30,000 HUF / month");
});

test("test_ac6_low_confidence_plan_says_every_transfer_needs_approval", async () => {
  start(LOW_CONFIDENCE_PLAN);
  expect(
    await screen.findByRole("heading", { name: "Every transfer needs your approval" }),
  ).toBeInTheDocument();
  expect(screen.getByText(LOW_CONFIDENCE_PLAN.explanations[1] ?? "")).toBeInTheDocument();
  expect(
    within(screen.getByRole("complementary", { name: "Summary" })).getByText("Low confidence"),
  ).toBeInTheDocument();
});

test("shows the time machine summary and links to the month-by-month view", async () => {
  start();
  expect(await screen.findAllByText("147,000 HUF saved · 1 month skipped")).toHaveLength(2); // card + panel
  expect(screen.getByRole("link", { name: "See month by month" })).toHaveAttribute(
    "href",
    "/plans/7/time-machine",
  );
});

test("rejects a decimal amount without calling the API", async () => {
  const { calls, user } = start();
  const field = await screen.findByLabelText("Monthly amount");
  await user.clear(field);
  await user.type(field, "100.5");
  await user.click(screen.getByRole("button", { name: "Update plan" }));
  expect(field).toHaveAttribute("aria-invalid", "true");
  expect(calls.filter((c) => c.method === "PATCH")).toEqual([]);
});

test("updating the amount sends a whole number and shows the revised plan", async () => {
  const { calls, user } = start(PLAN, {
    "PATCH /api/plans/7": { body: plan({ monthly_amount: 50_000 }) },
  });
  const field = await screen.findByLabelText("Monthly amount");
  await user.clear(field);
  await user.type(field, "50 000");
  await user.click(screen.getByRole("button", { name: "Update plan" }));
  expect(calls.find((c) => c.method === "PATCH")?.body).toEqual({ monthly_amount: 50_000 });
  expect(
    await within(screen.getByRole("complementary", { name: "Summary" })).findByText("50,000 HUF"),
  ).toBeInTheDocument();
});

test("test_ac8_amount_above_proposal_shows_the_server_message", async () => {
  const { user } = start(PLAN, {
    "PATCH /api/plans/7": {
      status: 422,
      body: {
        detail: "The monthly amount must be between 1 and 73500 HUF.",
        field: "monthly_amount",
      },
    },
  });
  const field = await screen.findByLabelText("Monthly amount");
  await user.clear(field);
  await user.type(field, "80000");
  await user.click(screen.getByRole("button", { name: "Update plan" }));
  expect(
    await screen.findByText("The monthly amount must be between 1 and 73500 HUF."),
  ).toBeInTheDocument();
});

test("test_ac7_rejecting_goes_home_without_orders", async () => {
  const { calls, user } = start(PLAN, {
    "POST /api/plans/7/reject": { body: plan({ status: "rejected" }) },
  });
  await user.click(await screen.findByRole("button", { name: "Reject plan" }));
  expect(await screen.findByText("Navigated to /")).toBeInTheDocument();
  expect(calls.some((c) => c.path.endsWith("/accept"))).toBe(false);
});

test("an accepted plan offers no edit or signing", async () => {
  start(plan({ status: "accepted", mandate_version: 1 }));
  expect(await screen.findByRole("link", { name: "Go to your savings plan" })).toHaveAttribute(
    "href",
    "/plan",
  );
  expect(screen.queryByRole("button", { name: "Update plan" })).toBeNull();
  expect(screen.queryByRole("link", { name: "Continue to mandate" })).toBeNull();
});
