import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { ApiError } from "../../api/client";
import { useEditPlan, usePlan, usePlanAction, useTimeMachine } from "../../api/hooks";
import type { PlanOut } from "../../api/types";
import { Badge, confidenceBadge } from "../../components/Badge";
import { Button, buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { Icon } from "../../components/Icon";
import { PlanItemCard } from "../../components/PlanItemCard";
import { SavedChart } from "../../components/SavedChart";
import { SummaryPanel } from "../../components/SummaryPanel";
import { TextField } from "../../components/TextField";
import { formatHuf, parseHuf } from "../../format";
import { machineSummary } from "./machineSummary";

function Facts({ plan }: { plan: PlanOut }) {
  const rows: [string, string][] = [
    [
      "Median monthly surplus",
      plan.median_surplus === null ? "Your own estimate" : formatHuf(plan.median_surplus),
    ],
    ["Share saved", `${plan.share_percent}%`],
    ["Months analysed", String(plan.months_of_data)],
    ["Risk score", String(plan.risk_score)],
    ["Minimum balance kept", formatHuf(plan.min_balance)],
  ];
  return (
    <dl className="mt-4 space-y-2">
      {rows.map(([term, value]) => (
        <div key={term} className="flex justify-between text-body">
          <dt className="text-text-muted">{term}</dt>
          <dd className="font-semibold">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function SaveLess({ plan }: { plan: PlanOut }) {
  const edit = useEditPlan(plan.id);
  const [text, setText] = useState(String(plan.monthly_amount));
  const [invalid, setInvalid] = useState(false);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const amount = parseHuf(text);
    if (amount === null || amount === 0) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    edit.mutate(amount);
  }

  const serverError =
    edit.error instanceof ApiError && edit.error.field === "monthly_amount"
      ? edit.error.message
      : null;
  return (
    <Card title="Want to save less?">
      <form className="flex flex-col gap-3 md:flex-row md:items-start" onSubmit={submit} noValidate>
        <TextField
          className="flex-1"
          label="Monthly amount"
          inputMode="numeric"
          suffix="HUF"
          value={text}
          error={invalid ? "Enter a positive whole amount in forints." : serverError}
          hint={`Between 1 and ${formatHuf(plan.proposed_amount)}. A lower amount creates a revised plan; nothing runs until you accept it.`}
          onChange={(e) => setText(e.target.value)}
        />
        <Button type="submit" variant="secondary" className="md:mt-7" disabled={edit.isPending}>
          Update plan
        </Button>
      </form>
      {serverError ? null : <ErrorMessage error={edit.error} />}
    </Card>
  );
}

/** Figma 05 Plan review (7:282) and 05b low confidence (10:709), step 3 of 4. */
export function PlanReviewScreen() {
  const planId = Number(useParams().planId);
  const navigate = useNavigate();
  const plan = usePlan(planId);
  const machine = useTimeMachine(planId);
  const reject = usePlanAction("reject");
  const data = plan.data;
  const proposed = data?.status === "proposed";

  return (
    <FlowLayout step={3} title="Plan review" backTo={`/plans/${planId}/analysis`} wide>
      <ErrorMessage error={plan.error} />
      {data ? (
        <div className="flex flex-col gap-6 lg:flex-row">
          <div className="flex-1 space-y-6">
            <header>
              <h1 className="text-h1">Your savings plan</h1>
              <p className="text-text-muted">
                {proposed
                  ? `Proposed ${data.created_on}. Not active until you sign the mandate.`
                  : `This plan is ${data.status}.`}
              </p>
              {proposed ? null : (
                <Link to="/plan" className={`${buttonClass("secondary")} mt-3`}>
                  Go to your savings plan
                </Link>
              )}
            </header>
            <Card title="Why this amount">
              <p className="text-body">{data.explanations[0]}</p>
              <Facts plan={data} />
            </Card>
            {data.per_transfer_approval ? (
              <section className="flex gap-3 rounded-lg border border-warning bg-warning-bg p-4 text-warning">
                <Icon name="alert" />
                <div>
                  <h2 className="text-h3">Every transfer needs your approval</h2>
                  {data.explanations.slice(1).map((text) => (
                    <p key={text} className="text-body">
                      {text}
                    </p>
                  ))}
                </div>
              </section>
            ) : null}
            <Card title="Where the money goes, in priority order">
              <ul aria-label="Plan items" className="space-y-3">
                {data.items.map((item) => (
                  <PlanItemCard key={item.position} item={item} number={item.position + 1} />
                ))}
              </ul>
              <p className="mt-3 text-caption text-text-muted">
                Risk score {data.risk_score} from your answers: no product above risk{" "}
                {data.risk_score} is used. Items with nothing left to fund are not shown.
              </p>
            </Card>
            <Card>
              <h2 className="flex items-center gap-2 text-h3">
                <Icon name="history" />
                Time machine: this plan on your last {machine.data?.months_replayed ?? ""} months
              </h2>
              <ErrorMessage error={machine.error} />
              {machine.data ? (
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <SavedChart months={machine.data.months} compact />
                  <div>
                    <p className="text-h2">{machineSummary(machine.data)}</p>
                    <p className="mt-2 text-body text-text-muted">
                      Past behaviour only, not a forecast.
                    </p>
                  </div>
                </div>
              ) : null}
              <Link to={`/plans/${planId}/time-machine`} className={`${buttonClass("ghost")} mt-4`}>
                <Icon name="chevron-right" />
                See month by month
              </Link>
            </Card>
            {proposed ? <SaveLess plan={data} /> : null}
            {proposed ? (
              <div>
                <ErrorMessage error={reject.error} />
                <Button
                  variant="danger"
                  disabled={reject.isPending}
                  onClick={() => reject.mutate(planId, { onSuccess: () => navigate("/") })}
                >
                  Reject plan
                </Button>
              </div>
            ) : null}
          </div>
          {proposed ? (
            <SummaryPanel
              label="Monthly amount"
              value={
                <>
                  <span>{formatHuf(data.monthly_amount)}</span>{" "}
                  <span className="text-body font-normal text-text-muted">/ month</span>
                </>
              }
              badge={
                <Badge tone={confidenceBadge(data.confidence).tone}>
                  {confidenceBadge(data.confidence).label}
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
                    <dd className="font-semibold">{data.next_transfer_on}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-text-muted">Minimum balance kept</dt>
                    <dd className="font-semibold">{formatHuf(data.min_balance)}</dd>
                  </div>
                </dl>
              }
              action={
                <Link to={`/plans/${planId}/mandate`} className={buttonClass("primary")}>
                  Continue to mandate
                </Link>
              }
              note="Nothing runs until you sign the mandate."
            />
          ) : null}
        </div>
      ) : null}
    </FlowLayout>
  );
}
