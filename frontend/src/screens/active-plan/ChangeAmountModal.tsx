import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { ApiError } from "../../api/client";
import { useRevisePlan } from "../../api/hooks";
import type { PlanOut } from "../../api/types";
import { Button } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Modal } from "../../components/Modal";
import { TextField } from "../../components/TextField";
import { formatHuf, parseHuf } from "../../format";

/** "Change amount" on Figma 08: proposes a revision; signing it creates the next mandate version. */
export function ChangeAmountModal({ plan, onClose }: { plan: PlanOut; onClose: () => void }) {
  const navigate = useNavigate();
  const revise = useRevisePlan(plan.id);
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
    revise.mutate(amount, { onSuccess: (revision) => navigate(`/plans/${revision.id}`) });
  }

  const fieldError =
    revise.error instanceof ApiError && revise.error.field === "monthly_amount"
      ? revise.error.message
      : null;
  return (
    <Modal title="Change the monthly amount" onClose={onClose}>
      <form className="space-y-4" onSubmit={submit} noValidate>
        <p className="text-body">
          Your current plan keeps running until you sign the new amount. Signing pauses mandate
          version {plan.mandate_version} and signs a new version.
        </p>
        <TextField
          label="New monthly amount"
          inputMode="numeric"
          suffix="HUF"
          value={text}
          error={invalid ? "Enter a positive whole amount in forints." : fieldError}
          hint={`Between 1 and ${formatHuf(plan.proposed_amount)}.`}
          onChange={(e) => setText(e.target.value)}
        />
        {fieldError ? null : <ErrorMessage error={revise.error} />}
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={revise.isPending}>
            Propose new amount
          </Button>
        </div>
      </form>
    </Modal>
  );
}
