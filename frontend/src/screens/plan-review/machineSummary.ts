import type { TimeMachineOut } from "../../api/types";
import { formatHuf } from "../../format";

/** "147,000 HUF saved · 1 month skipped" (plan review card and summary panels). */
export function machineSummary(machine: TimeMachineOut): string {
  const skipped = machine.skipped_months.length;
  return `${formatHuf(machine.total_saved)} saved · ${skipped} ${skipped === 1 ? "month" : "months"} skipped`;
}
