import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { useAcceptPlan, useMandate, usePlan, useTimeMachine } from "../../api/hooks";
import type { MandateOut, PlanOut } from "../../api/types";
import { Badge, confidenceBadge } from "../../components/Badge";
import { Button, buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { Checkbox } from "../../components/Checkbox";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { SummaryPanel } from "../../components/SummaryPanel";
import { formatDay, formatHuf } from "../../format";
import { machineSummary } from "../plan-review/machineSummary";
import { ConfirmSignModal } from "./ConfirmSignModal";

const CONSENT = "I have read the mandate and authorise these recurring orders.";

function Terms({ mandate }: { mandate: MandateOut }) {
  const rows: [string, string][] = [
    ["Monthly maximum (total)", formatHuf(mandate.max_monthly_amount)],
    ["Minimum balance kept", formatHuf(mandate.min_balance)],
    ["Allowed products", mandate.products.map((p) => p.name).join(", ")],
    [
      "Per-transfer approval",
      mandate.per_transfer_approval ? "On (low confidence)" : "Off (high confidence)",
    ],
  ];
  return (
    <dl className="space-y-2 rounded-md bg-surface-hover p-4">
      {rows.map(([term, value]) => (
        <div key={term} className="flex justify-between gap-4 text-body">
          <dt className="text-text-muted">{term}</dt>
          <dd className="text-right font-semibold">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function WhatHappens({ plan }: { plan: PlanOut }) {
  const lines = [
    "Your recurring orders are created once. Signing again creates no duplicates.",
    `The first transfers run on ${plan.next_transfer_on}, each checked against this mandate first.`,
    "You can pause at any time (§4).",
    "Changing the amount later creates a new mandate version; this version stays in the log.",
  ];
  return (
    <Card title="What happens when you sign">
      <ul className="list-disc space-y-1 pl-5 text-body">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </Card>
  );
}

/** Figma 07 Mandate (8:422) and 07b password confirmation (8:550), step 4 of 4 (AC7). */
export function MandateScreen() {
  const planId = Number(useParams().planId);
  const navigate = useNavigate();
  const plan = usePlan(planId);
  const machine = useTimeMachine(planId);
  const mandate = useMandate(planId);
  const accept = useAcceptPlan(planId);
  const [consent, setConsent] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const m = mandate.data;
  const p = plan.data;
  const unsigned = m?.status === "unsigned";

  return (
    <FlowLayout step={4} title="Mandate" backTo={`/plans/${planId}`} wide>
      <ErrorMessage error={mandate.error ?? plan.error} />
      {m && p ? (
        <div className="flex flex-col gap-6 lg:flex-row">
          <div className="flex-1 space-y-6">
            <header>
              <h1 className="text-h1">{unsigned ? "Sign your mandate" : "Your mandate"}</h1>
              <p className="text-text-muted">
                Orders run only within these limits. Every executed order is logged with the mandate
                version and the clause that allowed it.
              </p>
            </header>
            <Card>
              <h2 className="mb-4 text-h2">Mandate · version {m.version}</h2>
              {unsigned ? null : (
                <p className="mb-4 text-body font-semibold">
                  Version {m.version}, signed {formatDay(m.signed_at ?? "")}
                </p>
              )}
              <Terms mandate={m} />
              <ol className="mt-4 space-y-3">
                {m.clauses.map((clause) => (
                  <li key={clause.number} className="flex gap-3 text-body">
                    <span className="rounded-sm bg-surface-hover px-2 py-0.5 text-caption font-semibold">
                      §{clause.number}
                    </span>
                    <span>{clause.text}</span>
                  </li>
                ))}
              </ol>
              {unsigned ? (
                <div className="mt-4 rounded-md border border-border">
                  <Checkbox
                    label={CONSENT}
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                  />
                </div>
              ) : (
                <Link to="/plan" className={`${buttonClass("secondary")} mt-4`}>
                  Go to your savings plan
                </Link>
              )}
            </Card>
            {unsigned ? <WhatHappens plan={p} /> : null}
          </div>
          {unsigned ? (
            <SummaryPanel
              label="You are signing"
              value={
                <>
                  <span>{formatHuf(m.max_monthly_amount)}</span>{" "}
                  <span className="text-body font-normal text-text-muted">/ month</span>
                </>
              }
              badge={
                <Badge tone={confidenceBadge(p.confidence).tone}>
                  {confidenceBadge(p.confidence).label}
                </Badge>
              }
              details={
                <dl className="space-y-2 text-body">
                  {machine.data ? (
                    <div>
                      <dt className="text-caption text-text-muted">
                        Time machine, last {machine.data.months_replayed} months
                      </dt>
                      <dd className="font-semibold">{machineSummary(machine.data)}</dd>
                    </div>
                  ) : null}
                  <div className="flex justify-between">
                    <dt className="text-text-muted">First transfer</dt>
                    <dd className="font-semibold">{p.next_transfer_on}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-text-muted">Minimum balance kept</dt>
                    <dd className="font-semibold">{formatHuf(m.min_balance)}</dd>
                  </div>
                </dl>
              }
              action={
                <Button disabled={!consent} onClick={() => setConfirming(true)}>
                  Sign mandate
                </Button>
              }
              note="You confirm with your password in the next step."
            />
          ) : null}
        </div>
      ) : null}
      {confirming && m ? (
        <ConfirmSignModal
          mandate={m}
          pending={accept.isPending}
          error={accept.error}
          onClose={() => {
            accept.reset();
            setConfirming(false);
          }}
          onConfirm={(password) => accept.mutate(password, { onSuccess: () => navigate("/plan") })}
        />
      ) : null}
    </FlowLayout>
  );
}
