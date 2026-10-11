import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { expect, test, vi } from "vitest";
import { AppShell } from "./AppShell";
import { Button } from "./Button";
import { FlowHeader } from "./FlowHeader";
import { Modal } from "./Modal";
import { SideNav } from "./SideNav";
import { SummaryPanel } from "./SummaryPanel";

const ANNA = { username: "anna", role: "customer" as const };

test("SideNav marks the current page and shows the user", () => {
  render(
    <MemoryRouter initialEntries={["/plan"]}>
      <SideNav user={ANNA} onLogout={vi.fn()} />
    </MemoryRouter>,
  );
  expect(screen.getByRole("link", { name: "Savings plan" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  expect(screen.getByRole("link", { name: "Home" })).not.toHaveAttribute("aria-current");
  expect(screen.getByText("Anna")).toBeInTheDocument();
  expect(screen.getByText("Simulated bank data")).toBeInTheDocument();
});

test("SideNav logs out", async () => {
  const onLogout = vi.fn();
  render(
    <MemoryRouter>
      <SideNav user={ANNA} onLogout={onLogout} />
    </MemoryRouter>,
  );
  await userEvent.setup().click(screen.getByRole("button", { name: "Log out" }));
  expect(onLogout).toHaveBeenCalledOnce();
});

test("AppShell menu button opens and Esc closes the drawer", async () => {
  render(
    <MemoryRouter>
      <AppShell user={ANNA} onLogout={vi.fn()}>
        <p>Content</p>
      </AppShell>
    </MemoryRouter>,
  );
  const user = userEvent.setup();
  const menu = screen.getByRole("button", { name: "Open menu" });
  expect(menu).toHaveAttribute("aria-expanded", "false");
  await user.click(menu);
  expect(menu).toHaveAttribute("aria-expanded", "true");
  expect(document.getElementById("drawer")).not.toBeNull();
  await user.keyboard("{Escape}");
  expect(menu).toHaveAttribute("aria-expanded", "false");
});

test("FlowHeader shows the step, back and exit", () => {
  render(
    <MemoryRouter>
      <FlowHeader step={3} title="Plan review" backTo="/plans/7/analysis" />
    </MemoryRouter>,
  );
  expect(screen.getByText("Step 3 of 4")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Back" })).toHaveAttribute("href", "/plans/7/analysis");
  expect(screen.getByRole("link", { name: "Save & exit" })).toHaveAttribute("href", "/");
  expect(screen.getByRole("progressbar", { name: "Plan steps" })).toHaveAttribute(
    "aria-valuenow",
    "3",
  );
});

test("SummaryPanel renders its action once", () => {
  render(
    <SummaryPanel
      label="Monthly amount"
      value="73,500 HUF"
      details={<p>Details</p>}
      action={<Button>Continue to mandate</Button>}
    />,
  );
  expect(screen.getAllByRole("button", { name: "Continue to mandate" })).toHaveLength(1);
  expect(screen.getByRole("complementary", { name: "Summary" })).toBeInTheDocument();
});

test("Modal focuses its field, traps Tab and closes on Esc", async () => {
  const onClose = vi.fn();
  render(
    <>
      <button type="button">Outside</button>
      <Modal title="Confirm with your password" onClose={onClose}>
        <label>
          Password
          <input type="password" />
        </label>
        <button type="button">Confirm and sign</button>
      </Modal>
    </>,
  );
  const user = userEvent.setup();
  expect(screen.getByRole("dialog", { name: "Confirm with your password" })).toHaveAttribute(
    "aria-modal",
    "true",
  );
  expect(screen.getByLabelText("Password")).toHaveFocus();
  await user.tab(); // Confirm and sign
  await user.tab(); // Close (×)
  await user.tab(); // wraps to the field, never "Outside"
  expect(screen.getByLabelText("Password")).toHaveFocus();
  await user.keyboard("{Escape}");
  expect(onClose).toHaveBeenCalledOnce();
});
