/** Figma StatTile (frame 3:191): label, big value, optional caption. */
export function StatTile({
  label,
  value,
  caption,
}: {
  label: string;
  value: string;
  caption?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-caption text-text-muted">{label}</p>
      <p className="mt-1 text-h1">{value}</p>
      {caption ? <p className="mt-1 text-caption text-text-muted">{caption}</p> : null}
    </div>
  );
}
