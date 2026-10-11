import type { QuestionnaireIn } from "../../api/types";
import { AMOUNT_HINT, parseHuf } from "../../format";

export interface ExpenseDraft {
  name: string;
  amount: string;
  dueOn: string;
}

export interface Draft {
  fund: string;
  risk: number | null;
  expenses: ExpenseDraft[];
}

/** Keys are the backend field names, so server errors (ApiError.field) land in the same map. */
export type FieldErrors = Record<string, string>;

export const EMPTY_DRAFT: Draft = { fund: "", risk: null, expenses: [] };

export const POSITIVE_HINT = "Enter a positive whole amount in forints.";

/** Parse the typed answers. Only shape checks: business rules (past dates) are the server's. */
export function toAnswers(
  draft: Draft,
  expected: number | null,
): { answers: QuestionnaireIn } | { errors: FieldErrors } {
  const errors: FieldErrors = {};
  const fund = parseHuf(draft.fund);
  if (fund === null) errors.existing_emergency_fund = AMOUNT_HINT;
  if (draft.risk === null) errors.risk_score = "Choose how much risk you accept.";
  const expenses = draft.expenses.map((row, index) => {
    const amount = parseHuf(row.amount);
    if (row.name.trim() === "") errors[`planned_expenses.${index}.name`] = "Name the expense.";
    if (amount === null || amount === 0) errors[`planned_expenses.${index}.amount`] = POSITIVE_HINT;
    if (row.dueOn === "") errors[`planned_expenses.${index}.due_on`] = "Pick a due date.";
    return { name: row.name.trim(), amount: amount ?? 0, due_on: row.dueOn };
  });
  if (Object.keys(errors).length > 0 || fund === null || draft.risk === null) return { errors };
  return {
    answers: {
      risk_score: draft.risk,
      existing_emergency_fund: fund,
      expected_monthly_savings: expected,
      planned_expenses: expenses,
    },
  };
}
