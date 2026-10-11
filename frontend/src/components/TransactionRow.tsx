import type { TransactionOut } from "../api/types";
import { formatSigned } from "../format";

/** Figma TransactionRow (frame 3:191). */
export function TransactionRow({ transaction }: { transaction: TransactionOut }) {
  const description = transaction.description || "Transaction";
  const meta = transaction.own_transfer
    ? `${transaction.booked_on} · Own transfer, ignored in surplus`
    : transaction.booked_on;
  return (
    <li className="flex min-h-touch items-center gap-3 border-b border-border py-3 last:border-b-0">
      <span
        aria-hidden="true"
        className="flex size-8 items-center justify-center rounded-full bg-primary-subtle text-caption text-primary"
      >
        {description.charAt(0)}
      </span>
      <div className="flex-1">
        <p className="text-body font-semibold">{description}</p>
        <p className="text-caption text-text-muted">{meta}</p>
      </div>
      <p className="text-body font-semibold">{formatSigned(transaction.amount)}</p>
    </li>
  );
}
