import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { PLAN } from "../../test/fixtures";
import { mockApi, renderScreen, type Call } from "../../test/render";
import { QuestionnaireScreen } from "./QuestionnaireScreen";

const PROPOSAL = { outcome: "plan", plan: PLAN, explanations: PLAN.explanations };

/** Writes only: the screen also reads /api/rules. */
function posts(calls: Call[]): Call[] {
  return calls.filter((call) => call.method === "POST");
}

function start(routes = {}) {
  const calls = mockApi({
    "GET /api/rules": {
      body: {
        lines: [
          "a",
          "b",
          "Money needed within 12 months goes only to low-risk, liquid products.",
          "d",
        ],
      },
    },
    "POST /api/questionnaire": { status: 201, body: { id: 1 } },
    "POST /api/plans": { body: PROPOSAL },
    ...routes,
  });
  renderScreen(<QuestionnaireScreen />, { path: "/questionnaire" });
  return { calls, user: userEvent.setup() };
}

test("submits the answers and opens the spending analysis", async () => {
  const { calls, user } = start();
  await user.type(screen.getByLabelText("Existing emergency fund"), "720,000");
  await user.click(screen.getByRole("radio", { name: "2 Low" }));
  await user.click(screen.getByRole("button", { name: "Add an expense" }));
  await user.type(screen.getByLabelText("What for"), "New laptop");
  await user.type(screen.getByLabelText("Amount"), "300 000");
  await user.type(screen.getByLabelText("Due date"), "2027-08-01");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(await screen.findByText("Navigated to /plans/7/analysis")).toBeInTheDocument();
  expect(posts(calls).map((c) => c.path)).toEqual(["/api/questionnaire", "/api/plans"]);
  expect(posts(calls)[0]?.body).toEqual({
    risk_score: 2,
    existing_emergency_fund: 720_000,
    expected_monthly_savings: null,
    planned_expenses: [{ name: "New laptop", amount: 300_000, due_on: "2027-08-01" }],
  });
});

test("rejects a decimal emergency fund without calling the API", async () => {
  const { calls, user } = start();
  await user.type(screen.getByLabelText("Existing emergency fund"), "100.5");
  await user.click(screen.getByRole("radio", { name: "3 Medium" }));
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(screen.getByLabelText("Existing emergency fund")).toHaveAccessibleDescription(
    "Whole forints. Cannot be negative. Money you can reach at short notice. Enter 0 if you have none.",
  );
  expect(posts(calls)).toEqual([]);
});

test("requires a risk score", async () => {
  const { calls, user } = start();
  await user.type(screen.getByLabelText("Existing emergency fund"), "0");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(await screen.findByText("Choose how much risk you accept.")).toBeInTheDocument();
  expect(posts(calls)).toEqual([]);
});

test("a negative expense amount shows a field error without calling the API", async () => {
  const { calls, user } = start();
  await user.type(screen.getByLabelText("Existing emergency fund"), "0");
  await user.click(screen.getByRole("radio", { name: "3 Medium" }));
  await user.click(screen.getByRole("button", { name: "Add an expense" }));
  await user.type(screen.getByLabelText("What for"), "Holiday");
  await user.type(screen.getByLabelText("Amount"), "-50,000");
  await user.type(screen.getByLabelText("Due date"), "2027-01-01");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(screen.getByLabelText("Amount")).toHaveAttribute("aria-invalid", "true");
  expect(screen.getByText("Enter a positive whole amount in forints.")).toBeInTheDocument();
  expect(posts(calls)).toEqual([]);
});

test("an expense row can be removed", async () => {
  const { user } = start();
  await user.click(screen.getByRole("button", { name: "Add an expense" }));
  await user.click(screen.getByRole("button", { name: "Remove expense 1" }));
  expect(screen.queryByLabelText("What for")).toBeNull();
});
