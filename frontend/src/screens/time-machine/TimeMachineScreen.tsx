import { Link, useParams } from "react-router";
import { usePlan, useTimeMachine } from "../../api/hooks";
import type { BacktestMonthOut, TimeMachineOut } from "../../api/types";
import { Badge } from "../../components/Badge";
import { buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { Icon } from "../../components/Icon";
import { SavedChart } from "../../components/SavedChart";
import { StatTile } from "../../components/StatTile";
import { formatHuf, formatMonth } from "../../format";

const list = new Intl.ListFormat("en", { style: "long", type: "conjunction" });

function Legend() {
  return (
    <ul className="flex flex-wrap gap-4 text-caption text-text-muted">
      <li className="flex items-center gap-1.5">
        <span aria-hidden="true" className="size-3 rounded-sm bg-chart-saved" />
        Saved to date
      </li>
      <li className="flex items-center gap-1.5">
        <span
          aria-hidden="true"
          className="size-3 rounded-sm border border-dashed border-chart-skipped bg-chart-income"
        />
        Skipped: no transfer, total unchanged
      </li>
    </ul>
  );
}

function MonthRow({ m }: { m: BacktestMonthOut }) {
  return (
    <tr className={`border-t border-border ${m.skipped ? "bg-warning-bg" : ""}`}>
      <th scope="row" className="px-3 py-3 text-left font-semibold">
        {formatMonth(m.month)}
      </th>
      <td className="hidden px-3 py-3 text-right md:table-cell">
        {formatHuf(m.balance_before_transfer)}
      </td>
      <td className="px-3 py-3 text-right">{formatHuf(m.transfer)}</td>
      <td className="hidden px-3 py-3 text-right md:table-cell">{formatHuf(m.balance_after)}</td>
      <td className="px-3 py-3 text-right font-semibold">{formatHuf(m.saved_to_date)}</td>
      <td className="px-3 py-3">
        {m.skipped ? <Badge tone="warning">Skipped</Badge> : <Badge tone="success">Transfer</Badge>}
      </td>
    </tr>
  );
}

function MonthTable({ months }: { months: BacktestMonthOut[] }) {
  return (
    <table className="w-full text-body">
      <caption className="sr-only">Month by month replay of the plan</caption>
      <thead className="text-caption text-text-muted">
        <tr>
          <th scope="col" className="px-3 pb-2 text-left font-medium">
            Month
          </th>
          <th scope="col" className="hidden px-3 pb-2 text-right font-medium md:table-cell">
            Balance before
          </th>
          <th scope="col" className="px-3 pb-2 text-right font-medium">
            Transfer
          </th>
          <th scope="col" className="hidden px-3 pb-2 text-right font-medium md:table-cell">
            Balance after
          </th>
          <th scope="col" className="px-3 pb-2 text-right font-medium">
            Saved to date
          </th>
          <th scope="col" className="px-3 pb-2 text-left font-medium">
            Status
          </th>
        </tr>
      </thead>
      <tbody>
        {months.map((m) => (
          <MonthRow key={m.month} m={m} />
        ))}
      </tbody>
    </table>
  );
}

function SkippedMonths({ machine }: { machine: TimeMachineOut }) {
  const skipped = machine.months.filter((m) => m.skipped);
  return (
    <Card>
      <h2 className="mb-3 flex items-center gap-2 text-h2">
        Skipped months <Badge tone="warning">{skipped.length}</Badge>
      </h2>
      {skipped.length === 0 ? (
        <p className="text-body text-text-muted">No transfer would have been skipped.</p>
      ) : (
        <ul className="space-y-3">
          {skipped.map((m) => (
            <li
              key={m.month}
              className="flex gap-3 rounded-md bg-warning-bg px-4 py-3 text-body text-warning"
            >
              <Icon name="alert" />
              <span className="flex-1 text-text">{m.note}</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

/** Figma 06 Financial time machine (7:452): sub-view of step 3, AC4. */
export function TimeMachineScreen() {
  const planId = Number(useParams().planId);
  const plan = usePlan(planId);
  const machine = useTimeMachine(planId);
  const data = machine.data;

  return (
    <FlowLayout step={3} title="Plan review · time machine" backTo={`/plans/${planId}`} wide>
      <div className="space-y-6">
        <header>
          <h1 className="text-h1">Financial time machine</h1>
          <p className="text-text-muted">
            What would have happened if this plan had run on your last {data?.months_replayed ?? ""}{" "}
            months of real transactions? This shows past behaviour only, not a forecast.
          </p>
        </header>
        <ErrorMessage error={machine.error} />
        <ErrorMessage error={plan.error} />
        {data ? (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <StatTile
                label={`Saved over ${data.months_replayed} months`}
                value={formatHuf(data.total_saved)}
                caption={
                  plan.data
                    ? `${formatHuf(plan.data.monthly_amount)} a month when it ran`
                    : undefined
                }
              />
              <StatTile
                label="Transfers made"
                value={`${data.transfers_made} of ${data.months_replayed}`}
                caption={
                  plan.data
                    ? `Each one within the ${formatHuf(plan.data.min_balance)} minimum`
                    : undefined
                }
              />
              <StatTile
                label="Months skipped"
                value={String(data.skipped_months.length)}
                caption={list.format(data.skipped_months.map(formatMonth)) || undefined}
              />
            </div>
            <Card>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-h2">Saved to date, month by month</h2>
                <Legend />
              </div>
              <SavedChart months={data.months} />
              <p className="mt-4 text-caption text-text-muted">
                Value labels appear on hover or keyboard focus, not on every bar.
              </p>
            </Card>
            <Card title="Month by month">
              <MonthTable months={data.months} />
            </Card>
            <SkippedMonths machine={data} />
          </>
        ) : null}
        {plan.data?.status === "proposed" ? (
          <div className="flex justify-end">
            <Link to={`/plans/${planId}/mandate`} className={buttonClass("primary")}>
              Continue to mandate
            </Link>
          </div>
        ) : null}
      </div>
    </FlowLayout>
  );
}
