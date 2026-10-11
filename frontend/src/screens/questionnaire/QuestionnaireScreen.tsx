import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { ApiError } from "../../api/client";
import { useRules, useSubmitAnswers } from "../../api/hooks";
import type { ProposalOut } from "../../api/types";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { Kbd } from "../../components/Kbd";
import { TextField } from "../../components/TextField";
import { EMPTY_DRAFT, toAnswers, type Draft, type FieldErrors } from "./answers";
import { ExpenseRows } from "./ExpenseRows";
import { NoSurplusView } from "./NoSurplusView";
import { RiskOptions } from "./RiskOptions";
import { TooLittleDataView } from "./TooLittleDataView";

/** Figma 03 Questionnaire (6:169), step 1 of 4. */
export function QuestionnaireScreen() {
  const navigate = useNavigate();
  const submit = useSubmitAnswers();
  const rules = useRules();
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [outcome, setOutcome] = useState<ProposalOut | null>(null);

  function send(expected: number | null) {
    const parsed = toAnswers(draft, expected);
    if ("errors" in parsed) {
      setErrors(parsed.errors);
      return;
    }
    setErrors({});
    submit.mutate(parsed.answers, {
      onSuccess: (proposal) => {
        if (proposal.outcome === "plan" && proposal.plan) {
          // With an expected amount there is no history to analyse: go straight to the plan.
          navigate(
            expected === null
              ? `/plans/${proposal.plan.id}/analysis`
              : `/plans/${proposal.plan.id}`,
          );
          return;
        }
        setOutcome(proposal);
      },
      onError: (error) => {
        if (error instanceof ApiError && error.field) setErrors({ [error.field]: error.message });
      },
    });
  }

  // A field error is shown at the field, so the form-level alert shows only the others.
  const formError = submit.error instanceof ApiError && submit.error.field ? null : submit.error;

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    send(null);
  }

  // 09 and 10 live on /questionnaire, so a Back link would point to the same URL: the
  // "Change my answers" button returns to the form with the draft kept.
  if (outcome?.outcome === "no_surplus") {
    return (
      <FlowLayout step={2} title="Spending analysis" backTo={null}>
        <NoSurplusView explanations={outcome.explanations} />
        <Button variant="secondary" className="mt-4" onClick={() => setOutcome(null)}>
          Change my answers
        </Button>
      </FlowLayout>
    );
  }
  if (outcome?.outcome === "needs_expected_savings") {
    return (
      <FlowLayout step={2} title="Spending analysis" backTo={null}>
        <TooLittleDataView
          explanations={outcome.explanations}
          pending={submit.isPending}
          error={formError}
          fieldError={errors.expected_monthly_savings}
          onSubmit={(expected) => send(expected)}
        />
        <Button variant="secondary" className="mt-4" onClick={() => setOutcome(null)}>
          Change my answers
        </Button>
      </FlowLayout>
    );
  }

  return (
    <FlowLayout step={1} title="Your answers" backTo="/">
      <form className="space-y-6" onSubmit={onSubmit} noValidate>
        <header>
          <h1 className="text-h1">Tell us about your situation</h1>
          <p className="text-text-muted">
            Three fixed questions. Your answers set the emergency-fund gap, the risk limit and the
            planned expenses in your plan.
          </p>
          <p className="mt-3 flex flex-wrap items-center gap-2 text-caption text-text-muted">
            <Kbd>Tab</Kbd> moves between fields <Kbd>←</Kbd> <Kbd>→</Kbd> change the risk score{" "}
            <Kbd>Enter ↵</Kbd> continues
          </p>
        </header>
        <Card title="1. How much do you already have in an emergency fund?">
          <TextField
            label="Existing emergency fund"
            inputMode="numeric"
            suffix="HUF"
            value={draft.fund}
            error={errors.existing_emergency_fund}
            hint="Money you can reach at short notice. Enter 0 if you have none."
            onChange={(e) => setDraft({ ...draft, fund: e.target.value })}
          />
        </Card>
        <Card title="2. How much risk are you comfortable with?">
          <fieldset>
            <legend className="mb-3 text-body text-text-muted">
              1 = I never want to see a loss · 5 = I accept large swings for a higher long-term
              return. Products above your score never appear in the plan.
            </legend>
            <RiskOptions
              value={draft.risk}
              error={errors.risk_score}
              onChange={(risk) => setDraft({ ...draft, risk })}
            />
          </fieldset>
        </Card>
        <Card title="3. Any large expenses planned?">
          {/* lines[2] is the liquid-horizon rule, filled from RuleConfig (not hard-coded "12 months"). */}
          <p className="mb-4 text-body text-text-muted">{rules.data?.lines[2]}</p>
          <ExpenseRows
            rows={draft.expenses}
            errors={errors}
            onChange={(expenses) => setDraft({ ...draft, expenses })}
          />
        </Card>
        <ErrorMessage error={formError} />
        <div className="flex items-center justify-end gap-3">
          <span className="text-caption text-text-muted">
            or press <Kbd>Enter ↵</Kbd>
          </span>
          <Button type="submit" disabled={submit.isPending}>
            Continue
          </Button>
        </div>
      </form>
    </FlowLayout>
  );
}
