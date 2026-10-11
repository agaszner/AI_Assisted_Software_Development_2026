import type { ReactNode } from "react";
import { FlowHeader } from "./FlowHeader";

interface FlowLayoutProps {
  step: 1 | 2 | 3 | 4;
  title: string;
  backTo: string | null;
  children: ReactNode;
  /** Two-column screens (plan review, mandate) use the full 1040 px; forms use 720 px. */
  wide?: boolean;
}

export function FlowLayout({ step, title, backTo, children, wide = false }: FlowLayoutProps) {
  return (
    <div className="min-h-screen">
      <FlowHeader step={step} title={title} backTo={backTo} />
      <main
        className={`mx-auto w-full px-4 pt-8 pb-32 lg:pb-12 ${wide ? "max-w-content" : "max-w-narrow"}`}
      >
        {children}
      </main>
    </div>
  );
}
