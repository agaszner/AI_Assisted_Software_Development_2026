import type { ReactNode } from "react";

/** White card, radius-lg, border (every Figma content block). */
export function Card({
  title,
  children,
  className = "",
}: {
  title?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-lg border border-border bg-surface p-6 ${className}`}>
      {title ? <h2 className="mb-4 text-h3">{title}</h2> : null}
      {children}
    </section>
  );
}
