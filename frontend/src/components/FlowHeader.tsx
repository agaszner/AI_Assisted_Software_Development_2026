import { Link } from "react-router";
import { buttonClass } from "./Button";
import { Icon } from "./Icon";

const STEPS = [1, 2, 3, 4] as const;

/** Figma FlowHeader (frame 3:79): plan flow without sidebar. Compact below 768 px (10:982). */
export function FlowHeader({
  step,
  title,
  backTo,
}: {
  step: 1 | 2 | 3 | 4;
  title: string;
  backTo: string | null;
}) {
  return (
    <header className="flex h-14 items-center justify-between gap-4 border-b border-border bg-surface px-4 md:h-18 md:px-6">
      <div className="flex items-center gap-4">
        <p className="hidden items-center gap-2 text-h3 md:flex">
          <span
            aria-hidden="true"
            className="flex size-8 items-center justify-center rounded-md bg-primary text-on-primary"
          >
            S
          </span>
          SaverAI
        </p>
        {backTo ? (
          <Link to={backTo} aria-label="Back" className={buttonClass("ghost")}>
            <Icon name="arrow-left" />
            <span className="hidden md:inline">Back</span>
          </Link>
        ) : null}
      </div>
      <div className="text-center">
        <p className="text-caption text-text-muted">
          Step {step} of 4 <span className="hidden font-semibold text-text md:inline">{title}</span>
        </p>
        <div
          role="progressbar"
          aria-label="Plan steps"
          aria-valuemin={1}
          aria-valuemax={4}
          aria-valuenow={step}
          className="mt-1 flex gap-1"
        >
          {STEPS.map((n) => (
            <span
              key={n}
              className={`h-1 w-9 rounded-full ${n <= step ? "bg-primary" : "bg-border"}`}
            />
          ))}
        </div>
      </div>
      <Link to="/" className={buttonClass("secondary")}>
        Save &amp; exit
      </Link>
    </header>
  );
}
