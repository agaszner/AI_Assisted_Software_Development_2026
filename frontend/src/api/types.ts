/**
 * Mirror of backend/api/schemas.py (after backend Tasks 2–5). Keep field names and enum values
 * identical. Dates are ISO strings ("2026-09-01"); datetimes are ISO strings with time.
 */

/** Whole forints. Always an integer; the frontend never does arithmetic on money. */
export type Huf = number;

export type Role = "customer" | "admin";

export interface Me {
  username: string;
  role: Role;
}

export interface LoginIn {
  username: string;
  password: string;
}

export interface ExpenseIn {
  name: string;
  amount: Huf;
  due_on: string;
}

export interface QuestionnaireIn {
  risk_score: number;
  existing_emergency_fund: Huf;
  expected_monthly_savings: Huf | null;
  planned_expenses: ExpenseIn[];
}

export interface IdOut {
  id: number;
}

export type Confidence = "none" | "low" | "normal";
export type PlanStatus = "proposed" | "accepted" | "rejected" | "paused";
export type Outcome = "plan" | "no_surplus" | "needs_expected_savings";
export type ItemKind = "emergency_fund" | "planned_expense" | "investment";

export interface ProductOut {
  id: number;
  name: string;
  risk_level: number;
  liquid: boolean;
}

export interface PlanItemOut {
  position: number;
  kind: ItemKind;
  label: string;
  product: ProductOut;
  monthly_amount: Huf;
  target_amount: Huf | null;
  due_on: string | null;
  saved_amount: Huf;
  progress_percent: number | null;
}

export interface PlanOut {
  id: number;
  status: PlanStatus;
  revises: number | null;
  pending_revision: number | null;
  created_on: string;
  monthly_amount: Huf;
  proposed_amount: Huf;
  median_surplus: Huf | null;
  months_of_data: number;
  share_percent: number;
  risk_score: number;
  min_balance: Huf;
  confidence: Confidence;
  per_transfer_approval: boolean;
  next_transfer_on: string;
  mandate_version: number | null;
  signed_on: string | null;
  saved_total: Huf;
  items: PlanItemOut[];
  explanations: string[];
}

export interface ProposalOut {
  outcome: Outcome;
  plan: PlanOut | null;
  explanations: string[];
}

export interface MonthOut {
  month: string;
  income: Huf;
  expenses: Huf;
  surplus: Huf;
}

export interface AnalysisOut {
  months_of_data: number;
  confidence: Confidence;
  median_surplus: Huf | null;
  median_expenses: Huf;
  monthly_amount: Huf | null;
  share_percent: number;
  median_explanation: string | null;
  explanations: string[];
  months: MonthOut[];
}

export interface BacktestMonthOut {
  month: string;
  balance_before_transfer: Huf;
  transfer: Huf;
  skipped: boolean;
  balance_after: Huf;
  saved_to_date: Huf;
  note: string | null;
}

export interface TimeMachineOut {
  total_saved: Huf;
  months_replayed: number;
  transfers_made: number;
  skipped_months: string[];
  months: BacktestMonthOut[];
}

export type ExecutionStatus = "executed" | "denied" | "awaiting_approval";

export interface ExecutionOut {
  id: number;
  period: string;
  status: ExecutionStatus;
  amount: Huf;
  mandate_version: number;
  clause: number;
  reason: string;
}

export type ActivityStatus =
  "scheduled" | ExecutionStatus | "proposed" | "done" | "rejected" | "paused";

export interface ActivityOut {
  key: string;
  on: string;
  title: string;
  amount: Huf | null;
  status: ActivityStatus;
  mandate_version: number | null;
  clause: string | null;
  idempotency_key: string | null;
  logged_at: string | null;
  execution_id: number | null;
}

export interface TransactionOut {
  id: number;
  booked_on: string;
  amount: Huf;
  description: string;
  own_transfer: boolean;
}

export interface AccountOut {
  today: string;
  name: string;
  balance: Huf;
  min_balance: Huf;
  transactions: TransactionOut[];
}

export interface RulesOut {
  lines: string[];
}

export interface ClauseOut {
  number: number;
  text: string;
}

export type MandateStatus = "unsigned" | "active" | "paused";

export interface MandateOut {
  status: MandateStatus;
  version: number;
  signed_at: string | null;
  max_monthly_amount: Huf;
  min_balance: Huf;
  per_transfer_approval: boolean;
  products: ProductOut[];
  clauses: ClauseOut[];
}
