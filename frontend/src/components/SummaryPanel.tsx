import type { ReactNode } from "react";

interface SummaryPanelProps {
  label: string;
  value: ReactNode;
  badge?: ReactNode;
  details?: ReactNode;
  action: ReactNode;
  note?: string;
}

/**
 * Figma "Sticky summary panel" (3:261): from 1024 px a 360 px card, position sticky, top 24 px;
 * below 1024 px a fixed bottom action bar with the value, the badge and the main button
 * (details and note hidden). One DOM tree, so the action exists once.
 */
export function SummaryPanel({ label, value, badge, details, action, note }: SummaryPanelProps) {
  return (
    <aside
      aria-label="Summary"
      className="fixed inset-x-0 bottom-0 z-30 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-border bg-surface p-4 shadow-panel lg:sticky lg:top-6 lg:block lg:w-panel lg:shrink-0 lg:self-start lg:rounded-lg lg:border lg:p-6"
    >
      <div className="flex w-full items-center justify-between gap-3">
        <p className="text-caption text-text-muted">{label}</p>
        {badge}
      </div>
      <div className="flex-1 text-h2 lg:mt-1 lg:text-number">{value}</div>
      {details ? (
        <div className="mt-4 hidden space-y-3 border-t border-border pt-4 lg:block">{details}</div>
      ) : null}
      <div className="lg:mt-4 lg:grid">{action}</div>
      {note ? (
        <p className="mt-3 hidden text-center text-caption text-text-muted lg:block">{note}</p>
      ) : null}
    </aside>
  );
}
