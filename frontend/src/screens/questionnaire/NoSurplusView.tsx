import { Link } from "react-router";
import { useAnalysis } from "../../api/hooks";
import { buttonClass } from "../../components/Button";
import { Icon } from "../../components/Icon";
import { StatTile } from "../../components/StatTile";
import { formatHuf } from "../../format";

/** Figma 09 No surplus (10:791), AC5: an explanation instead of an investment. */
export function NoSurplusView({ explanations }: { explanations: string[] }) {
  const analysis = useAnalysis();
  const median = analysis.data?.median_surplus;
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-surface p-8 text-center">
        <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-info-bg text-info">
          <Icon name="info" />
        </span>
        <h1 className="mt-4 text-h1">No surplus to save right now</h1>
        {explanations.map((text) => (
          <p key={text} role="status" className="mt-2 text-text-muted">
            {text}
          </p>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <StatTile
          label="Median monthly surplus"
          value={median === null || median === undefined ? "—" : formatHuf(median)}
        />
        <StatTile label="Months analysed" value={String(analysis.data?.months_of_data ?? "—")} />
        <StatTile label="Orders created" value="None" />
      </div>
      <Link to="/" className={buttonClass("primary")}>
        Back to home
      </Link>
    </div>
  );
}
