import { Link, useParams } from "react-router";
import { useAnalysis } from "../../api/hooks";
import type { Confidence } from "../../api/types";
import { buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { StatTile } from "../../components/StatTile";
import { formatHuf, formatMonth } from "../../format";
import { SurplusChart } from "./SurplusChart";

const CONFIDENCE_CAPTION: Record<Confidence, string> = {
  normal: "Enough for a full-confidence plan",
  low: "Low confidence: every transfer needs your approval",
  none: "Too few months for an estimate",
};

/** Figma 04 Spending analysis (6:305), step 2 of 4. */
export function AnalysisScreen() {
  const planId = Number(useParams().planId);
  const analysis = useAnalysis();
  const data = analysis.data;
  const title = `Monthly surplus, last ${data?.months.length ?? ""} months`;

  return (
    <FlowLayout step={2} title="Spending analysis" backTo="/questionnaire" wide>
      <div className="space-y-6">
        <header>
          <h1 className="text-h1">Your spending analysis</h1>
          <p className="text-text-muted">
            Surplus = income − expenses per calendar month. Transfers between your own accounts are
            ignored. The median limits the effect of one-off months.
          </p>
        </header>
        <ErrorMessage error={analysis.error} />
        {data ? (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <StatTile
                label="Median monthly surplus"
                value={data.median_surplus === null ? "—" : formatHuf(data.median_surplus)}
                caption={`Last ${data.months.length} complete months`}
              />
              <StatTile
                label="Suggested monthly amount"
                value={data.monthly_amount === null ? "—" : formatHuf(data.monthly_amount)}
                caption={`${data.share_percent}% of the median`}
              />
              <StatTile
                label="Months analysed"
                value={String(data.months_of_data)}
                caption={CONFIDENCE_CAPTION[data.confidence]}
              />
            </div>
            <Card title={title}>
              <SurplusChart months={data.months} median={data.median_surplus} />
              {data.median_explanation ? (
                <p className="mt-4 text-body text-text-muted">{data.median_explanation}</p>
              ) : null}
              <details className="mt-4">
                <summary className="flex min-h-touch cursor-pointer items-center text-body font-semibold text-primary">
                  See month by month
                </summary>
                <table className="mt-2 w-full text-left text-body">
                  <caption className="sr-only">{title}</caption>
                  <thead>
                    <tr className="text-caption text-text-muted">
                      <th className="py-2">Month</th>
                      <th>Income</th>
                      <th>Expenses</th>
                      <th>Surplus</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.months.map((m) => (
                      <tr key={m.month} className="border-t border-border">
                        <td className="py-2">{formatMonth(m.month)}</td>
                        <td>{formatHuf(m.income)}</td>
                        <td>{formatHuf(m.expenses)}</td>
                        <td className="font-semibold">{formatHuf(m.surplus)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            </Card>
            <div className="flex justify-end">
              <Link to={`/plans/${planId}`} className={buttonClass("primary")}>
                See my plan
              </Link>
            </div>
          </>
        ) : null}
      </div>
    </FlowLayout>
  );
}
