import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { ActivityOut } from "../api/types";
import { mockApi, renderScreen } from "../test/render";
import { ExecutionLog } from "./ExecutionLog";

const SCHEDULED: ActivityOut = {
  key: "scheduled-1-2026-11",
  on: "2026-11-01",
  title: "30,000 HUF to your emergency fund",
  amount: 30_000,
  status: "scheduled",
  mandate_version: 1,
  clause: "Will be checked against §1 and §2",
  idempotency_key: "order-1-2026-11",
  logged_at: null,
  execution_id: null,
};
const WAITING: ActivityOut = {
  ...SCHEDULED,
  key: "execution-5",
  on: "2026-10-01",
  status: "awaiting_approval",
  clause: "§3 · This transfer needs your approval.",
  idempotency_key: "order-1-2026-10",
  logged_at: "2026-10-06T12:00:00Z",
  execution_id: 5,
};

test("a row opens its audit details", async () => {
  mockApi({});
  renderScreen(<ExecutionLog rows={[SCHEDULED]} />);
  const user = userEvent.setup();
  const toggle = screen.getByRole("button", {
    name: "Audit details: 30,000 HUF to your emergency fund",
  });
  expect(toggle).toHaveAttribute("aria-expanded", "false");
  await user.click(toggle);
  expect(toggle).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByText("order-1-2026-11")).toBeInTheDocument();
  expect(screen.getByText("Will be checked against §1 and §2")).toBeInTheDocument();
  expect(screen.getByText("Not run yet")).toBeInTheDocument();
  expect(screen.getByText("Scheduled")).toBeInTheDocument();
});

test("test_ac6_waiting_transfer_can_be_approved", async () => {
  const calls = mockApi({
    "POST /api/executions/5/approve": { body: { id: 5, status: "executed" } },
  });
  renderScreen(<ExecutionLog rows={[WAITING]} />);
  const user = userEvent.setup();
  expect(screen.getByText("Needs approval")).toBeInTheDocument();
  await user.click(
    screen.getByRole("button", { name: "Approve 30,000 HUF to your emergency fund" }),
  );
  expect(calls.filter((c) => c.method === "POST").map((c) => c.path)).toEqual([
    "/api/executions/5/approve",
  ]);
});

test("an empty log says so", () => {
  mockApi({});
  renderScreen(<ExecutionLog rows={[]} />);
  expect(screen.getByText("Nothing has happened yet.")).toBeInTheDocument();
  expect(within(document.body).queryByRole("table")).toBeNull();
});
