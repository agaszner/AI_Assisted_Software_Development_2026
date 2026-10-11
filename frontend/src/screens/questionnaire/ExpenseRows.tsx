import { Button } from "../../components/Button";
import { TextField } from "../../components/TextField";
import type { ExpenseDraft, FieldErrors } from "./answers";

const EMPTY_ROW: ExpenseDraft = { name: "", amount: "", dueOn: "" };
const MAX_ROWS = 10; // QuestionnaireIn.planned_expenses max_length

export function ExpenseRows({
  rows,
  errors,
  onChange,
}: {
  rows: ExpenseDraft[];
  errors: FieldErrors;
  onChange: (rows: ExpenseDraft[]) => void;
}) {
  function update(index: number, change: Partial<ExpenseDraft>) {
    onChange(rows.map((row, i) => (i === index ? { ...row, ...change } : row)));
  }
  return (
    <div className="space-y-4">
      {rows.map((row, index) => (
        <div key={index} className="grid items-start gap-3 md:grid-cols-4">
          <TextField
            label="What for"
            value={row.name}
            maxLength={100}
            error={errors[`planned_expenses.${index}.name`]}
            onChange={(e) => update(index, { name: e.target.value })}
          />
          <TextField
            label="Amount"
            inputMode="numeric"
            suffix="HUF"
            value={row.amount}
            error={errors[`planned_expenses.${index}.amount`]}
            onChange={(e) => update(index, { amount: e.target.value })}
          />
          <TextField
            label="Due date"
            type="date"
            value={row.dueOn}
            error={errors[`planned_expenses.${index}.due_on`]}
            onChange={(e) => update(index, { dueOn: e.target.value })}
          />
          <Button
            variant="ghost"
            aria-label={`Remove expense ${index + 1}`}
            className="md:mt-7"
            onClick={() => onChange(rows.filter((_, i) => i !== index))}
          >
            Remove
          </Button>
        </div>
      ))}
      {rows.length < MAX_ROWS ? (
        <Button variant="ghost" onClick={() => onChange([...rows, EMPTY_ROW])}>
          {rows.length === 0 ? "Add an expense" : "Add another expense"}
        </Button>
      ) : null}
    </div>
  );
}
