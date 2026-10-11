import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Badge, confidenceBadge, statusBadge } from "./Badge";
import { Button } from "./Button";
import { Checkbox } from "./Checkbox";
import { ErrorMessage } from "./ErrorMessage";
import { Icon } from "./Icon";
import { ProgressBar } from "./ProgressBar";
import { StatTile } from "./StatTile";
import { TextField } from "./TextField";
import { TransactionRow } from "./TransactionRow";

test("Button defaults to type=button with the touch target and focus ring", () => {
  render(<Button>Save</Button>);
  const button = screen.getByRole("button", { name: "Save" });
  expect(button).toHaveAttribute("type", "button");
  expect(button.className).toContain("min-h-touch");
  expect(button.className).toContain("focus-visible:shadow-focus");
});

test("TextField labels its input and links the error", () => {
  render(<TextField label="Monthly amount" suffix="HUF" error="Too much." hint="Whole forints." />);
  const input = screen.getByLabelText("Monthly amount");
  expect(input.className).toContain("min-h-touch");
  expect(input).toHaveAttribute("aria-invalid", "true");
  expect(input).toHaveAccessibleDescription("Too much. Whole forints.");
  expect(screen.getByText("HUF")).toBeInTheDocument();
});

test("Checkbox is labelled and reachable", () => {
  render(<Checkbox label="I have read the mandate" />);
  expect(screen.getByRole("checkbox", { name: "I have read the mandate" })).not.toBeChecked();
});

test("ErrorMessage shows Error and string messages, nothing for null", () => {
  const { rerender } = render(<ErrorMessage error={null} />);
  expect(screen.queryByRole("alert")).toBeNull();
  rerender(<ErrorMessage error={new Error("Plan not found.")} />);
  expect(screen.getByRole("alert")).toHaveTextContent("Plan not found.");
  rerender(<ErrorMessage error="Choose how much risk you accept." />);
  expect(screen.getByRole("alert")).toHaveTextContent("Choose how much risk you accept.");
});

test("badges map statuses and confidence to Figma tones", () => {
  expect(statusBadge("scheduled")).toEqual({ tone: "info", label: "Scheduled" });
  expect(statusBadge("executed")).toEqual({ tone: "success", label: "Done" });
  expect(statusBadge("awaiting_approval")).toEqual({ tone: "warning", label: "Needs approval" });
  expect(confidenceBadge("normal")).toEqual({ tone: "success", label: "High confidence" });
  expect(confidenceBadge("low")).toEqual({ tone: "warning", label: "Low confidence" });
  render(<Badge tone="success">Active</Badge>);
  expect(screen.getByText("Active")).toBeInTheDocument();
});

test("ProgressBar exposes its value", () => {
  render(<ProgressBar label="Emergency fund" percent={96} />);
  const bar = screen.getByRole("progressbar", { name: "Emergency fund" });
  expect(bar).toHaveAttribute("aria-valuenow", "96");
});

test("StatTile and Icon render", () => {
  render(
    <>
      <StatTile
        label="Median monthly surplus"
        value="105,000 HUF"
        caption="Last 6 complete months"
      />
      <Icon name="home" />
    </>,
  );
  expect(screen.getByText("105,000 HUF")).toBeInTheDocument();
  expect(document.querySelector("svg[aria-hidden='true']")).not.toBeNull();
});

test("TransactionRow signs amounts and explains own transfers", () => {
  render(
    <ul>
      <TransactionRow
        transaction={{
          id: 1,
          booked_on: "2026-09-10",
          amount: 550_000,
          description: "Salary",
          own_transfer: false,
        }}
      />
      <TransactionRow
        transaction={{
          id: 2,
          booked_on: "2026-09-25",
          amount: -30_000,
          description: "To own savings account",
          own_transfer: true,
        }}
      />
    </ul>,
  );
  expect(screen.getByText("+550,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("−30,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("2026-09-25 · Own transfer, ignored in surplus")).toBeInTheDocument();
});
