import { useState, type FormEvent } from "react";
import type { MandateOut } from "../../api/types";
import { Button } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Kbd } from "../../components/Kbd";
import { Modal } from "../../components/Modal";
import { TextField } from "../../components/TextField";
import { formatHuf } from "../../format";

interface Props {
  mandate: MandateOut;
  pending: boolean;
  error: unknown;
  onClose: () => void;
  onConfirm: (password: string) => void;
}

/** Figma 07b (8:670): simulated strong customer authentication before signing. */
export function ConfirmSignModal({ mandate, pending, error, onClose, onConfirm }: Props) {
  const [password, setPassword] = useState("");
  const products = mandate.products.map((p) => p.name).join(", ");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending || password === "") return; // Enter pressed twice sends one request
    onConfirm(password);
  }

  return (
    <Modal title="Confirm with your password" icon="lock" onClose={onClose}>
      <form className="space-y-4" onSubmit={submit}>
        <p className="text-body">
          You are signing mandate version {mandate.version}: up to{" "}
          {formatHuf(mandate.max_monthly_amount)} a month to the {products}, always keeping at least{" "}
          {formatHuf(mandate.min_balance)} on your account.
        </p>
        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          hint="Simulated strong customer authentication. No real bank is involved."
          onChange={(e) => setPassword(e.target.value)}
        />
        <ErrorMessage error={error} />
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={pending || password === ""}>
            Confirm and sign
          </Button>
        </div>
        <p className="flex items-center justify-end gap-2 text-caption text-text-muted">
          <Kbd>Esc</Kbd> cancels <Kbd>Enter ↵</Kbd> confirms
        </p>
      </form>
    </Modal>
  );
}
