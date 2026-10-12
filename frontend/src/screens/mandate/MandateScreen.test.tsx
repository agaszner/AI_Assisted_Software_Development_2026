import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { MandateOut } from "../../api/types";
import { MACHINE, PLAN, plan } from "../../test/fixtures";
import { mockApi, renderScreen, type Handler } from "../../test/render";
import { MandateScreen } from "./MandateScreen";

const CLAUSE_1 =
  "SaverAI may transfer only to the products listed in this mandate, at most the monthly maximum in total per calendar month.";
const UNSIGNED: MandateOut = {
  status: "unsigned",
  version: 1,
  signed_at: null,
  max_monthly_amount: 73_500,
  min_balance: 100_000,
  per_transfer_approval: false,
  products: [{ id: 1, name: "Short government bond fund", risk_level: 2, liquid: true }],
  clauses: [
    { number: 1, text: CLAUSE_1 },
    { number: 4, text: "No transfer runs while the mandate is paused." },
  ],
};

function start(
  mandate: MandateOut = UNSIGNED,
  accept: Handler = { body: plan({ status: "accepted", mandate_version: 1 }) },
) {
  const calls = mockApi({
    "GET /api/plans/7": {
      body: mandate.status === "unsigned" ? PLAN : plan({ status: "accepted", mandate_version: 1 }),
    },
    "GET /api/plans/7/time-machine": { body: MACHINE },
    "GET /api/plans/7/mandate": { body: mandate },
    "POST /api/plans/7/accept": accept,
  });
  renderScreen(<MandateScreen />, { path: "/plans/:planId/mandate", url: "/plans/7/mandate" });
  return { calls, user: userEvent.setup() };
}

async function openModal(user: ReturnType<typeof userEvent.setup>) {
  const sign = await screen.findByRole("button", { name: "Sign mandate" });
  expect(sign).toBeDisabled();
  await user.click(
    screen.getByRole("checkbox", {
      name: "I have read the mandate and authorise these recurring orders.",
    }),
  );
  await user.click(sign);
  return screen.getByRole("dialog", { name: "Confirm with your password" });
}

test("shows the terms and clauses from the API", async () => {
  start();
  expect(await screen.findByRole("heading", { name: "Mandate · version 1" })).toBeInTheDocument();
  expect(screen.getByText(CLAUSE_1)).toBeInTheDocument();
  expect(screen.getByText("Short government bond fund")).toBeInTheDocument();
  expect(screen.getByText("Off (high confidence)")).toBeInTheDocument();
});

test("test_ac7_signing_needs_consent_then_password", async () => {
  const { calls, user } = start();
  const dialog = await openModal(user);
  expect(
    within(dialog).getByText(/up to 73,500 HUF a month to the Short government bond fund/),
  ).toBeInTheDocument();
  await user.type(within(dialog).getByLabelText("Password"), "secret");
  await user.click(within(dialog).getByRole("button", { name: "Confirm and sign" }));
  expect(await screen.findByText("Navigated to /plan")).toBeInTheDocument();
  expect(calls.filter((c) => c.method === "POST")).toEqual([
    expect.objectContaining({ path: "/api/plans/7/accept", body: { password: "secret" } }),
  ]);
});

test("a wrong password keeps the modal open and shows the message", async () => {
  const { user } = start(UNSIGNED, { status: 403, body: { detail: "Incorrect password." } });
  const dialog = await openModal(user);
  await user.type(within(dialog).getByLabelText("Password"), "wrong");
  await user.keyboard("{Enter}");
  expect(await within(dialog).findByRole("alert")).toHaveTextContent("Incorrect password.");
  expect(screen.getByRole("dialog", { name: "Confirm with your password" })).toBeInTheDocument();
});

test("test_ac7_confirm_button_is_disabled_while_signing", async () => {
  const { calls, user } = start(UNSIGNED, () => new Promise(() => undefined)); // never answers
  const dialog = await openModal(user);
  await user.type(within(dialog).getByLabelText("Password"), "secret");
  const confirm = within(dialog).getByRole("button", { name: "Confirm and sign" });
  await user.click(confirm);
  await user.click(confirm);
  await user.keyboard("{Enter}");
  expect(confirm).toBeDisabled();
  expect(calls.filter((c) => c.method === "POST")).toHaveLength(1);
});

test("Esc closes the modal without signing", async () => {
  const { calls, user } = start();
  await openModal(user);
  await user.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(calls.filter((c) => c.method === "POST")).toEqual([]);
});

test("test_ac7_signed_mandate_offers_no_second_signing", async () => {
  start({ ...UNSIGNED, status: "active", signed_at: "2026-10-08T12:00:00Z" });
  expect(await screen.findByText("Version 1, signed 2026-10-08")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Sign mandate" })).toBeNull();
  expect(screen.getByRole("link", { name: "Go to your savings plan" })).toHaveAttribute(
    "href",
    "/plan",
  );
});
