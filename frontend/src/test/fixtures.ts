import type { AnalysisOut, PlanOut, TimeMachineOut } from "../api/types";

/** The Figma 05 plan for anna: 73,500 HUF from a 105,000 HUF median (AC1), split 30k/30k/13.5k. */
export const PLAN: PlanOut = {
  id: 7,
  status: "proposed",
  revises: null,
  pending_revision: null,
  created_on: "2026-10-08",
  monthly_amount: 73_500,
  proposed_amount: 73_500,
  median_surplus: 105_000,
  months_of_data: 6,
  share_percent: 70,
  risk_score: 2,
  min_balance: 100_000,
  confidence: "normal",
  per_transfer_approval: false,
  next_transfer_on: "2026-11-01",
  mandate_version: null,
  signed_on: null,
  saved_total: 0,
  items: [
    {
      position: 0,
      kind: "emergency_fund",
      label: "Emergency fund",
      product: { id: 1, name: "Short government bond fund", risk_level: 2, liquid: true },
      monthly_amount: 30_000,
      target_amount: 750_000,
      due_on: null,
      saved_amount: 720_000,
      progress_percent: 96,
    },
    {
      position: 1,
      kind: "planned_expense",
      label: "New laptop",
      product: { id: 1, name: "Short government bond fund", risk_level: 2, liquid: true },
      monthly_amount: 30_000,
      target_amount: 300_000,
      due_on: "2027-08-01",
      saved_amount: 0,
      progress_percent: 0,
    },
    {
      position: 2,
      kind: "investment",
      label: "Long-term investment",
      product: { id: 1, name: "Short government bond fund", risk_level: 2, liquid: true },
      monthly_amount: 13_500,
      target_amount: null,
      due_on: null,
      saved_amount: 0,
      progress_percent: null,
    },
  ],
  explanations: [
    "We suggest saving 73,500 HUF a month: 70% of your median monthly surplus of 105,000 HUF.",
  ],
};

export function plan(overrides: Partial<PlanOut> = {}): PlanOut {
  return { ...PLAN, ...overrides };
}

/** Figma 05b: dani, 4 months of data, low confidence (AC6). */
export const LOW_CONFIDENCE_PLAN: PlanOut = plan({
  id: 8,
  monthly_amount: 40_250,
  proposed_amount: 40_250,
  median_surplus: 57_500,
  months_of_data: 4,
  confidence: "low",
  per_transfer_approval: true,
  explanations: [
    "We suggest saving 40,250 HUF a month: 70% of your median monthly surplus of 57,500 HUF.",
    "This plan is based on only 4 months of data, so its confidence is low. Every transfer will ask for your approval.",
  ],
});

export const ANALYSIS: AnalysisOut = {
  months_of_data: 6,
  confidence: "normal",
  median_surplus: 105_000,
  median_expenses: 250_000,
  monthly_amount: 73_500,
  share_percent: 70,
  median_explanation:
    "Sorted: 80,000 · 90,000 · 100,000 · 110,000 · 120,000 · 300,000. Median = (100,000 + 110,000) / 2 = 105,000 HUF.",
  explanations: [],
  months: [
    ["2026-04-01", 100_000],
    ["2026-05-01", 120_000],
    ["2026-06-01", 80_000],
    ["2026-07-01", 110_000],
    ["2026-08-01", 90_000],
    ["2026-09-01", 300_000],
  ].map(([month, surplus]) => ({
    month: String(month),
    income: 400_000,
    expenses: 400_000 - Number(surplus),
    surplus: Number(surplus),
  })),
};

const SKIP_NOTE = (month: string) =>
  `${month}: the transfer was skipped because it would have left less than 100,000 HUF on your account.`;

/** An illustrative 3-month replay with one skipped month (AC4). */
export const MACHINE: TimeMachineOut = {
  total_saved: 147_000,
  months_replayed: 3,
  transfers_made: 2,
  skipped_months: ["2025-12-01"],
  months: [
    {
      month: "2025-10-01",
      balance_before_transfer: 400_000,
      transfer: 73_500,
      skipped: false,
      balance_after: 326_500,
      saved_to_date: 73_500,
      note: null,
    },
    {
      month: "2025-11-01",
      balance_before_transfer: 350_000,
      transfer: 73_500,
      skipped: false,
      balance_after: 276_500,
      saved_to_date: 147_000,
      note: null,
    },
    {
      month: "2025-12-01",
      balance_before_transfer: 150_000,
      transfer: 0,
      skipped: true,
      balance_after: 150_000,
      saved_to_date: 147_000,
      note: SKIP_NOTE("2025-12"),
    },
  ],
};
