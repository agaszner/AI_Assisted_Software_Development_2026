import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";
import type { MonthOut } from "../../api/types";
import { formatCompact, formatHuf, formatMonth, formatNumber } from "../../format";

interface Row {
  month: string;
  surplus: number;
}

function SurplusTooltip({ active, payload }: TooltipContentProps) {
  const row = payload?.[0]?.payload as Row | undefined;
  if (!active || row === undefined) return null;
  return (
    <div className="rounded-md bg-tooltip-bg px-3 py-2 text-caption text-on-primary">
      {row.month} · {formatHuf(row.surplus)}
    </div>
  );
}

/** Figma 04 chart: bars per month, dashed median line labelled in the gutter, values in a
 * tooltip on hover or keyboard focus (Recharts accessibilityLayer). Decorative for screen
 * readers: the table on the screen carries the same values. */
export function SurplusChart({ months, median }: { months: MonthOut[]; median: number | null }) {
  const rows: Row[] = months.map((m) => ({ month: formatMonth(m.month), surplus: m.surplus }));
  return (
    <div aria-hidden="true" className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={rows}
          accessibilityLayer
          margin={{ top: 16, right: 72, bottom: 0, left: 0 }}
        >
          <CartesianGrid vertical={false} stroke="var(--color-chart-grid)" />
          <XAxis dataKey="month" tickLine={false} axisLine={false} />
          <YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} width={48} />
          <Tooltip content={SurplusTooltip} cursor={{ fill: "var(--color-surface-hover)" }} />
          {median === null ? null : (
            <ReferenceLine
              y={median}
              stroke="var(--color-primary)"
              strokeDasharray="4 4"
              label={{
                value: `Median ${formatNumber(median)}`,
                position: "right",
                fill: "var(--color-primary)",
                fontSize: 12,
              }}
            />
          )}
          <Bar dataKey="surplus" fill="var(--color-chart-saved)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
