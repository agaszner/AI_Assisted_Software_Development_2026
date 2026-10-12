import { Fragment, useState } from "react";
import { useApproveExecution } from "../api/hooks";
import type { ActivityOut } from "../api/types";
import { formatDay, formatHuf } from "../format";
import { Badge, statusBadge } from "./Badge";
import { Button } from "./Button";
import { ErrorMessage } from "./ErrorMessage";
import { Icon } from "./Icon";

function loggedAt(iso: string | null): string {
  return iso === null ? "Not run yet" : `${formatDay(iso)} ${iso.slice(11, 16)} UTC`;
}

function Audit({ row }: { row: ActivityOut }) {
  const items: [string, string][] = [
    ["Mandate", row.mandate_version === null ? "—" : `Version ${row.mandate_version}`],
    ["Clause", row.clause ?? "—"],
    ["Idempotency key", row.idempotency_key ?? "—"],
    ["Logged at", loggedAt(row.logged_at)],
  ];
  return (
    <dl className="grid gap-4 bg-surface-hover p-4 md:grid-cols-4">
      {items.map(([term, value]) => (
        <div key={term}>
          <dt className="text-caption text-text-muted">{term}</dt>
          <dd className="text-body font-semibold break-all">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

/**
 * Figma "Execution log table row" (3:210): Date, Event, Amount, Status, expandable audit row.
 * From 768 px a table; below it each row stacks (date and status on top, event, amount).
 */
export function ExecutionLog({ rows }: { rows: ActivityOut[] }) {
  const [open, setOpen] = useState<string | null>(null);
  const approve = useApproveExecution();
  if (rows.length === 0) return <p className="text-text-muted">Nothing has happened yet.</p>;
  return (
    <>
      <ErrorMessage error={approve.error} />
      <table className="w-full text-left text-body max-md:block">
        <thead className="text-caption text-text-muted max-md:hidden">
          <tr className="bg-surface-hover">
            <th className="px-3 py-2">Date</th>
            <th className="px-3 py-2">Event</th>
            <th className="px-3 py-2 text-right">Amount</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">
              <span className="sr-only">Details</span>
            </th>
          </tr>
        </thead>
        <tbody className="max-md:block">
          {rows.map((row) => {
            const badge = statusBadge(row.status);
            const expanded = open === row.key;
            return (
              <Fragment key={row.key}>
                <tr className="border-t border-border max-md:grid max-md:grid-cols-2 max-md:gap-1 max-md:py-3">
                  <td className="px-3 py-3 text-text-muted">{row.on}</td>
                  <td className="px-3 py-3 font-semibold max-md:order-3 max-md:col-span-2">
                    {row.title}
                  </td>
                  <td className="px-3 py-3 text-right max-md:order-4 max-md:text-left">
                    {row.amount === null ? "—" : formatHuf(row.amount)}
                  </td>
                  <td className="px-3 py-3 max-md:order-2 max-md:text-right">
                    <Badge tone={badge.tone}>{badge.label}</Badge>
                  </td>
                  <td className="px-3 py-1 max-md:order-5 max-md:col-span-2">
                    <div className="flex items-center justify-end gap-2">
                      {row.status === "awaiting_approval" && row.execution_id !== null ? (
                        <Button
                          aria-label={`Approve ${row.title}`}
                          disabled={approve.isPending}
                          onClick={() => {
                            if (row.execution_id !== null) approve.mutate(row.execution_id);
                          }}
                        >
                          Approve
                        </Button>
                      ) : null}
                      <button
                        type="button"
                        aria-label={`Audit details: ${row.title}`}
                        aria-expanded={expanded}
                        onClick={() => setOpen(expanded ? null : row.key)}
                        className="flex size-touch items-center justify-center rounded-md outline-none hover:bg-surface-hover focus-visible:shadow-focus"
                      >
                        <Icon name={expanded ? "chevron-down" : "chevron-right"} />
                      </button>
                    </div>
                  </td>
                </tr>
                {expanded ? (
                  <tr className="max-md:block">
                    <td colSpan={5} className="max-md:block">
                      <Audit row={row} />
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </>
  );
}
