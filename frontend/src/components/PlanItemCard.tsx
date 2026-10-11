import type { PlanItemOut } from "../api/types";
import { formatHuf } from "../format";

function details(item: PlanItemOut): string {
  const product = `${item.product.name} · risk ${item.product.risk_level}${item.product.liquid ? " · liquid" : ""}`;
  if (item.kind === "emergency_fund" && item.target_amount !== null) {
    return `${product} · target ${formatHuf(item.target_amount)}, ${formatHuf(item.saved_amount)} already saved`;
  }
  if (item.kind === "planned_expense" && item.target_amount !== null) {
    return `${product} · ${formatHuf(item.target_amount)} needed by ${item.due_on ?? "the due date"}`;
  }
  return `${product} · the rest of the monthly amount`;
}

/** Figma PlanItem (frame 3:191): priority number, label, product line, monthly amount. */
export function PlanItemCard({ item, number }: { item: PlanItemOut; number: number }) {
  return (
    <li className="flex items-center gap-4 rounded-md border border-border p-4">
      <span
        aria-hidden="true"
        className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-caption text-on-primary"
      >
        {number}
      </span>
      <div className="flex-1">
        <p className="text-h3">
          {item.label}
          {item.due_on ? ` · due ${item.due_on}` : ""}
        </p>
        <p className="text-caption text-text-muted">{details(item)}</p>
      </div>
      <p className="text-body font-semibold whitespace-nowrap">
        {formatHuf(item.monthly_amount)} / month
      </p>
    </li>
  );
}
