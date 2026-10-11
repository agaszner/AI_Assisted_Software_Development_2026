import type { ReactNode } from "react";

/** Keyboard hint chip ("Tab", "Enter ↵") from Figma 03, 07b, 10. */
export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="rounded-sm border border-border-strong bg-surface px-1.5 py-0.5 font-sans text-caption">
      {children}
    </kbd>
  );
}
