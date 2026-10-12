import { useState } from "react";
import { Link } from "react-router";
import { useActivePlan, useActivity, usePlanAction } from "../../api/hooks";
import type { PlanOut } from "../../api/types";
import { Badge } from "../../components/Badge";
import { Button, buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { ExecutionLog } from "../../components/ExecutionLog";
import { Modal } from "../../components/Modal";
import { StatTile } from "../../components/StatTile";
import { formatHuf } from "../../format";
import { ChangeAmountModal } from "./ChangeAmountModal";

function Orders({ plan }: { plan: PlanOut }) {
  return (
    <Card title="Recurring orders">
      <ul aria-label="Recurring orders" className="space-y-2">
        {plan.items.map((item) => (
          <li
            key={item.position}
            className="flex items-center gap-4 rounded-md border border-border px-4 py-2"
          >
            <span
              aria-hidden="true"
              className="flex size-8 items-center justify-center rounded-full bg-primary text-caption text-on-primary"
            >
              {item.position + 1}
            </span>
            <div className="flex-1">
              <p className="text-body font-semibold">{item.label}</p>
              <p className="text-caption text-text-muted">
                {item.product.name} · {item.due_on ? `until ${item.due_on}` : "monthly on the 1st"}
              </p>
            </div>
            <p className="text-body font-semibold">{formatHuf(item.monthly_amount)} / month</p>
          </li>
        ))}
      </ul>
    </Card>
  );
}

/** Figma 08 Active plan (8:708). */
export function ActivePlanScreen() {
  const plan = useActivePlan();
  const activity = useActivity();
  const pause = usePlanAction("pause");
  const [dialog, setDialog] = useState<"pause" | "amount" | null>(null);
  const data = plan.data;

  if (plan.error) return <ErrorMessage error={plan.error} />;
  if (data === undefined) return <p>Loading…</p>;
  if (data === null) {
    return (
      <div className="space-y-4">
        <h1 className="text-h1">Your savings plan</h1>
        <p className="text-text-muted">You have no savings plan yet.</p>
        <Link to="/questionnaire" className={buttonClass("primary")}>
          Start a savings plan
        </Link>
      </div>
    );
  }
  const active = data.status === "accepted";
  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-3 text-h1">
            Your savings plan{" "}
            <Badge tone={active ? "success" : "warning"}>{active ? "Active" : "Paused"}</Badge>
          </h1>
          <p className="text-text-muted">
            Accepted {data.signed_on} under mandate version {data.mandate_version}.
          </p>
        </div>
        {active ? (
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setDialog("amount")}>
              Change amount
            </Button>
            <Button variant="danger" onClick={() => setDialog("pause")}>
              Pause plan
            </Button>
          </div>
        ) : null}
      </header>
      {data.pending_revision !== null ? (
        <section className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-info bg-info-bg p-4 text-info">
          <p className="text-body">
            A new amount is waiting for your signature. Your current plan keeps running until then.
          </p>
          <Link to={`/plans/${data.pending_revision}`} className={buttonClass("secondary")}>
            Review the new amount
          </Link>
        </section>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Monthly amount"
          value={formatHuf(data.monthly_amount)}
          caption={`${data.items.length} recurring orders`}
        />
        <StatTile
          label="Next transfer"
          value={active ? data.next_transfer_on : "—"}
          caption="Checked against the mandate first"
        />
        <StatTile
          label="Saved by SaverAI"
          value={formatHuf(data.saved_total)}
          caption={
            data.saved_total === 0 ? "First transfer has not run yet" : "Executed transfers so far"
          }
        />
        <StatTile
          label="Mandate"
          value={`Version ${data.mandate_version ?? "—"}`}
          caption={`Signed ${data.signed_on ?? "—"}`}
        />
      </div>
      <Orders plan={data} />
      <Card title="Execution log">
        <p className="mb-4 text-body text-text-muted">
          Every transfer is checked against your mandate before it runs. Open a row for the audit
          details.
        </p>
        <ErrorMessage error={activity.error} />
        {activity.data ? <ExecutionLog rows={activity.data} /> : null}
      </Card>
      {dialog === "pause" ? (
        <Modal title="Pause your savings plan?" onClose={() => setDialog(null)}>
          <p className="text-body">
            No transfer runs while the mandate is paused (§4). You can start a new plan later.
          </p>
          <ErrorMessage error={pause.error} />
          <div className="mt-4 flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setDialog(null)}>
              Keep it running
            </Button>
            <Button
              variant="danger"
              disabled={pause.isPending}
              onClick={() => pause.mutate(data.id, { onSuccess: () => setDialog(null) })}
            >
              Pause plan
            </Button>
          </div>
        </Modal>
      ) : null}
      {dialog === "amount" ? (
        <ChangeAmountModal plan={data} onClose={() => setDialog(null)} />
      ) : null}
    </div>
  );
}
