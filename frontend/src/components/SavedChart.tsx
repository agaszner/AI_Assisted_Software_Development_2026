import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";
import type { BacktestMonthOut } from "../api/types";
import { formatCompact, formatHuf, formatMonth, monthName } from "../format";

interface Row {
  month: string;
  label: string;
  saved: number;
  skipped: boolean;
}

function SavedTooltip({ active, payload }: TooltipContentProps) {
  const row = payload?.[0]?.payload as Row | undefined;
  if (!active || row === undefined) return null;
  return (
    <div className="max-w-60 rounded-md bg-tooltip-bg px-3 py-2 text-caption text-on-primary">
      <p className="font-semibold">
        {row.month}
        {row.skipped ? " · skipped" : ""}
      </p>
      <p>Saved to date {formatHuf(row.saved)}</p>
    </div>
  );
}

/**
 * Figma 06 chart: saved-to-date bars; a skipped month is a grey bar with a dashed amber outline
 * (the total did not grow). `compact` is the plan-review thumbnail: no axes, no tooltip.
 * Hidden from screen readers: the month table carries the same values (AC4).
 */
export function SavedChart({
  months,
  compact = false,
}: {
  months: BacktestMonthOut[];
  compact?: boolean;
}) {
  const rows: Row[] = months.map((m) => ({
    month: formatMonth(m.month),
    label: monthName(m.month),
    saved: m.saved_to_date,
    skipped: m.skipped,
  }));
  return (
    <div aria-hidden="true" className={compact ? "h-24" : "h-72"}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={rows}
          accessibilityLayer={!compact}
          margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
        >
          {compact ? null : <CartesianGrid vertical={false} stroke="var(--color-chart-grid)" />}
          {compact ? null : <XAxis dataKey="label" tickLine={false} axisLine={false} />}
          {compact ? null : (
            <YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} width={48} />
          )}
          {compact ? null : (
            <Tooltip content={SavedTooltip} cursor={{ fill: "var(--color-surface-hover)" }} />
          )}
          <Bar dataKey="saved" radius={[4, 4, 0, 0]}>
            {rows.map((row) => (
              <Cell
                key={row.month}
                fill={row.skipped ? "var(--color-chart-income)" : "var(--color-chart-saved)"}
                stroke={row.skipped ? "var(--color-chart-skipped)" : "none"}
                strokeDasharray={row.skipped ? "4 3" : undefined}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
