import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { ANALYSIS, plan } from "../../test/fixtures";
import { mockApi, renderScreen, type Handler } from "../../test/render";
import { QuestionnaireScreen } from "./QuestionnaireScreen";

const RULES = { body: { lines: ["a", "b", "c", "d"] } };
const NO_SURPLUS =
  "Your median monthly surplus over the last 6 months is -40,000 HUF, so there is no surplus to save. No investment plan was created.";
const TOO_LITTLE =
  "We found only 2 full months of transactions; at least 3 are needed for an estimate. Please enter how much you expect to save each month.";

async function answer(routes: Record<string, Handler>) {
  const calls = mockApi({
    "GET /api/rules": RULES,
    "POST /api/questionnaire": { status: 201, body: { id: 1 } },
    ...routes,
  });
  renderScreen(<QuestionnaireScreen />, { path: "/questionnaire" });
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Existing emergency fund"), "0");
  await user.click(screen.getByRole("radio", { name: "3 Medium" }));
  await user.click(screen.getByRole("button", { name: "Continue" }));
  return { calls, user };
}

test("test_ac5_no_surplus_shows_explanation_without_plan", async () => {
  await answer({
    "POST /api/plans": { body: { outcome: "no_surplus", plan: null, explanations: [NO_SURPLUS] } },
    "GET /api/analysis": {
      body: { ...ANALYSIS, median_surplus: -40_000, monthly_amount: 0, explanations: [NO_SURPLUS] },
    },
  });
  expect(
    await screen.findByRole("heading", { name: "No surplus to save right now" }),
  ).toBeInTheDocument();
  expect(screen.getByText(NO_SURPLUS)).toBeInTheDocument();
  expect(await screen.findByText("-40,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("None")).toBeInTheDocument(); // orders created
  expect(screen.getByRole("link", { name: "Back to home" })).toHaveAttribute("href", "/");
  expect(screen.queryByRole("button", { name: "Continue to mandate" })).toBeNull();
});

test("test_ac6_too_little_data_asks_for_expected_savings", async () => {
  let proposals = 0;
  const { calls, user } = await answer({
    "POST /api/plans": () => {
      proposals += 1;
      return proposals === 1
        ? { body: { outcome: "needs_expected_savings", plan: null, explanations: [TOO_LITTLE] } }
        : {
            body: { outcome: "plan", plan: plan({ id: 9, confidence: "none" }), explanations: [] },
          };
    },
  });
  expect(
    await screen.findByRole("heading", { name: "We need a little more data" }),
  ).toBeInTheDocument();
  expect(screen.getByText(TOO_LITTLE)).toBeInTheDocument();
  await user.type(screen.getByLabelText("Expected monthly savings"), "40000");
  await user.click(screen.getByRole("button", { name: "Show my plan" }));
  expect(await screen.findByText("Navigated to /plans/9")).toBeInTheDocument();
  const answers = calls.filter((c) => c.path === "/api/questionnaire").map((c) => c.body);
  expect(answers).toEqual([
    {
      risk_score: 3,
      existing_emergency_fund: 0,
      expected_monthly_savings: null,
      planned_expenses: [],
    },
    {
      risk_score: 3,
      existing_emergency_fund: 0,
      expected_monthly_savings: 40_000,
      planned_expenses: [],
    },
  ]);
});

test("too little data rejects an empty expected amount without calling the API", async () => {
  const { calls, user } = await answer({
    "POST /api/plans": {
      body: { outcome: "needs_expected_savings", plan: null, explanations: [TOO_LITTLE] },
    },
  });
  await screen.findByRole("heading", { name: "We need a little more data" });
  const before = calls.length;
  await user.click(screen.getByRole("button", { name: "Show my plan" }));
  expect(screen.getByLabelText("Expected monthly savings")).toHaveAttribute("aria-invalid", "true");
  expect(calls.length).toBe(before);
});

test("test_ac8_past_expense_date_shows_the_server_message_at_the_field", async () => {
  mockApi({
    "GET /api/rules": RULES,
    "POST /api/questionnaire": {
      status: 422,
      body: {
        detail: "The due date of 'Holiday' (2026-09-01) is in the past.",
        field: "planned_expenses.0.due_on",
      },
    },
  });
  renderScreen(<QuestionnaireScreen />, { path: "/questionnaire" });
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Existing emergency fund"), "0");
  await user.click(screen.getByRole("radio", { name: "3 Medium" }));
  await user.click(screen.getByRole("button", { name: "Add an expense" }));
  await user.type(screen.getByLabelText("What for"), "Holiday");
  await user.type(screen.getByLabelText("Amount"), "50000");
  await user.type(screen.getByLabelText("Due date"), "2026-09-01");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(
    await screen.findByText("The due date of 'Holiday' (2026-09-01) is in the past."),
  ).toBeInTheDocument();
  expect(screen.getByLabelText("Due date")).toHaveAttribute("aria-invalid", "true");
  expect(screen.queryByRole("alert")).toBeNull(); // shown at the field, not as a form error
});
