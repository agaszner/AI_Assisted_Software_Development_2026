import { Link } from "react-router";
import { useAccount, useActivePlan, useAnalysis, useMe, useRules } from "../../api/hooks";
import type { PlanItemOut, PlanOut } from "../../api/types";
import { Badge } from "../../components/Badge";
import { buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Icon } from "../../components/Icon";
import { ProgressBar } from "../../components/ProgressBar";
import { TransactionRow } from "../../components/TransactionRow";
import { displayName, formatHuf, formatNumber } from "../../format";

function itemCaption(item: PlanItemOut, plan: PlanOut): string {
  if (item.target_amount === null) {
    return `${formatHuf(item.monthly_amount)} a month · starts ${plan.next_transfer_on}`;
  }
  const saved = `${formatNumber(item.saved_amount)} of ${formatHuf(item.target_amount)}`;
  return item.due_on ? `${saved} · due ${item.due_on}` : saved;
}

function PlanCard({ plan }: { plan: PlanOut | null }) {
  if (plan === null) {
    return (
      <Card title="Your savings plan">
        <p className="text-text-muted">You have no savings plan yet.</p>
        <Link to="/questionnaire" className={`${buttonClass("primary")} mt-4 w-full`}>
          Start a savings plan
        </Link>
      </Card>
    );
  }
  return (
    <section className="rounded-lg border border-border bg-surface p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-h3">Your savings plan</h2>
        <Badge tone={plan.status === "accepted" ? "success" : "warning"}>
          {plan.status === "accepted" ? "Active" : "Paused"}
        </Badge>
      </div>
      <p className="mt-1 text-caption text-text-muted">
        {formatHuf(plan.monthly_amount)} a month · mandate v{plan.mandate_version}
      </p>
      <ul className="mt-4 space-y-4">
        {plan.items.map((item) => (
          <li key={item.position}>
            <div className="flex justify-between text-body font-semibold">
              <span>{item.label}</span>
              {item.progress_percent !== null ? (
                <span className="text-primary">{item.progress_percent}%</span>
              ) : null}
            </div>
            {item.progress_percent !== null ? (
              <div className="mt-2">
                <ProgressBar label={item.label} percent={item.progress_percent} />
              </div>
            ) : null}
            <p className="mt-1 text-caption text-text-muted">{itemCaption(item, plan)}</p>
          </li>
        ))}
      </ul>
      <Link to="/plan" className={`${buttonClass("secondary")} mt-4 w-full`}>
        View savings plan
      </Link>
    </section>
  );
}

/** Figma 02 Home (5:118). Every value comes from the API. */
export function HomeScreen() {
  const me = useMe();
  const account = useAccount();
  const plan = useActivePlan();
  const analysis = useAnalysis();
  const rules = useRules();

  const error = account.error ?? plan.error ?? analysis.error ?? rules.error;
  if (error) return <ErrorMessage error={error} />;
  if (!account.data || plan.data === undefined) return <p>Loading…</p>;

  const median = analysis.data?.median_surplus;
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-h1">Hello, {displayName(me.data?.username ?? "")}</h1>
        <p className="text-text-muted">
          Here is where your money stands today, {account.data.today}.
        </p>
      </header>
      <div className="grid gap-6 lg:grid-cols-5">
        <section className="flex flex-col justify-between gap-8 rounded-lg bg-primary p-6 text-on-primary lg:col-span-3">
          <div>
            <p className="text-body">Current account balance</p>
            <p className="mt-2">
              <span className="text-number">{formatNumber(account.data.balance)}</span>{" "}
              <span className="text-h3">HUF</span>
            </p>
            <p className="mt-1 text-caption">{account.data.name} · simulated</p>
          </div>
          <dl className="grid grid-cols-3 gap-4 text-caption">
            <div>
              <dt>Median monthly surplus</dt>
              <dd className="text-body font-semibold">
                {median === null || median === undefined ? "—" : formatHuf(median)}
              </dd>
            </div>
            <div>
              <dt>Minimum balance kept</dt>
              <dd className="text-body font-semibold">{formatHuf(account.data.min_balance)}</dd>
            </div>
            <div>
              <dt>Next transfer</dt>
              <dd className="text-body font-semibold">
                {plan.data?.status === "accepted" ? plan.data.next_transfer_on : "—"}
              </dd>
            </div>
          </dl>
        </section>
        <div className="lg:col-span-2">
          <PlanCard plan={plan.data} />
        </div>
        <Card title="Recent transactions" className="lg:col-span-3">
          <ul>
            {account.data.transactions.map((transaction) => (
              <TransactionRow key={transaction.id} transaction={transaction} />
            ))}
          </ul>
        </Card>
        <Card title="How the plan is calculated" className="lg:col-span-2">
          <ul className="space-y-3">
            {(rules.data?.lines ?? []).map((line) => (
              <li key={line} className="flex gap-2 text-body">
                <Icon name="chevron-right" className="mt-0.5 size-4 text-primary" />
                {line}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
