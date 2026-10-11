import type { ReactNode } from "react";
import type { ActivityStatus, Confidence } from "../api/types";

export type BadgeTone = "success" | "warning" | "info" | "neutral";

const TONES: Record<BadgeTone, string> = {
  success: "bg-success-bg text-success",
  warning: "bg-warning-bg text-warning",
  info: "bg-info-bg text-info",
  neutral: "bg-surface-hover text-text",
};

/** Figma Badges (frame 2:180): a dot and a short label. */
export function Badge({ tone, children }: { tone: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-caption ${TONES[tone]}`}
    >
      <span aria-hidden="true" className="size-1.5 rounded-full bg-current" />
      {children}
    </span>
  );
}

const STATUS: Record<ActivityStatus, { tone: BadgeTone; label: string }> = {
  scheduled: { tone: "info", label: "Scheduled" },
  executed: { tone: "success", label: "Done" },
  done: { tone: "success", label: "Done" },
  awaiting_approval: { tone: "warning", label: "Needs approval" },
  denied: { tone: "warning", label: "Skipped" },
  proposed: { tone: "neutral", label: "Proposed" },
  rejected: { tone: "neutral", label: "Rejected" },
  paused: { tone: "warning", label: "Paused" },
};

export function statusBadge(status: ActivityStatus): { tone: BadgeTone; label: string } {
  return STATUS[status];
}

const CONFIDENCE: Record<Confidence, { tone: BadgeTone; label: string }> = {
  normal: { tone: "success", label: "High confidence" },
  low: { tone: "warning", label: "Low confidence" },
  none: { tone: "warning", label: "Your own estimate" },
};

export function confidenceBadge(confidence: Confidence): { tone: BadgeTone; label: string } {
  return CONFIDENCE[confidence];
}
