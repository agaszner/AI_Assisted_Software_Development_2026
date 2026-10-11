import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import type { AccountOut } from "../../api/types";
import { ANALYSIS, PLAN, plan } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { HomeScreen } from "./HomeScreen";

const ACCOUNT: AccountOut = {
  today: "2026-10-08",
  name: "Main account",
  balance: 1_220_000,
  min_balance: 100_000,
  transactions: [
    { id: 1, booked_on: "2026-10-03", amount: -150_000, description: "Rent", own_transfer: false },
  ],
};
const RULES = { lines: ["Monthly amount = 70% of your median monthly surplus (last 6 months)."] };

function start(active: unknown) {
  mockApi({
    "GET /api/auth/me": { body: { username: "anna", role: "customer" } },
    "GET /api/account": { body: ACCOUNT },
    "GET /api/rules": { body: RULES },
    "GET /api/analysis": { body: ANALYSIS },
    "GET /api/plans/active":
      active === null ? { status: 404, body: { detail: "No active plan." } } : { body: active },
  });
  renderScreen(<HomeScreen />);
}

test("greets with the server date and shows the balance card", async () => {
  start(plan({ status: "accepted", mandate_version: 1 }));
  expect(await screen.findByRole("heading", { name: "Hello, Anna" })).toBeInTheDocument();
  expect(
    screen.getByText("Here is where your money stands today, 2026-10-08."),
  ).toBeInTheDocument();
  expect(screen.getByText("1,220,000")).toBeInTheDocument();
  expect(screen.getByText("105,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("100,000 HUF")).toBeInTheDocument();
  expect(await screen.findByText("2026-11-01")).toBeInTheDocument();
});

test("shows the plan with progress from the API", async () => {
  start(plan({ status: "accepted", mandate_version: 1 }));
  const card = (await screen.findByRole("heading", { name: "Your savings plan" })).closest(
    "section",
  );
  if (card === null) throw new Error("no plan card");
  const inCard = within(card);
  expect(inCard.getByText("73,500 HUF a month · mandate v1")).toBeInTheDocument();
  expect(inCard.getByRole("progressbar", { name: "Emergency fund" })).toHaveAttribute(
    "aria-valuenow",
    "96",
  );
  expect(inCard.getByText("720,000 of 750,000 HUF")).toBeInTheDocument();
  expect(inCard.getByText("0 of 300,000 HUF · due 2027-08-01")).toBeInTheDocument();
  expect(inCard.getByText("13,500 HUF a month · starts 2026-11-01")).toBeInTheDocument();
  expect(inCard.getByRole("link", { name: "View savings plan" })).toHaveAttribute("href", "/plan");
});

test("shows a start link when there is no active plan", async () => {
  start(null);
  expect(await screen.findByRole("link", { name: "Start a savings plan" })).toHaveAttribute(
    "href",
    "/questionnaire",
  );
});

test("renders transactions and the rule lines verbatim", async () => {
  start(PLAN);
  expect(await screen.findByText("Rent")).toBeInTheDocument();
  expect(await screen.findByText(RULES.lines[0] ?? "")).toBeInTheDocument();
});
