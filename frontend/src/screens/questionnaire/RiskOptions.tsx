const OPTIONS = [
  [1, "Lowest"],
  [2, "Low"],
  [3, "Medium"],
  [4, "High"],
  [5, "Highest"],
] as const;

/** Figma RiskOption (frame 2:182): native radios, so ← → change the score. */
export function RiskOptions({
  value,
  onChange,
  error,
}: {
  value: number | null;
  onChange: (risk: number) => void;
  error?: string;
}) {
  return (
    <div>
      <div className="grid grid-cols-5 gap-2">
        {OPTIONS.map(([score, name]) => (
          <label
            key={score}
            className={`flex min-h-touch cursor-pointer flex-col items-center justify-center rounded-md border px-2 py-3 has-focus-visible:shadow-focus ${value === score ? "border-primary bg-primary-subtle text-primary" : "border-border hover:bg-surface-hover"}`}
          >
            <input
              type="radio"
              name="risk"
              className="sr-only"
              aria-label={`${score} ${name}`}
              checked={value === score}
              onChange={() => onChange(score)}
            />
            <span className="text-h3">{score}</span>
            <span className="text-caption">{name}</span>
          </label>
        ))}
      </div>
      {error ? <p className="mt-2 text-caption text-danger">{error}</p> : null}
    </div>
  );
}
