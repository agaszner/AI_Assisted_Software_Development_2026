import { useState, type FormEvent } from "react";
import { Button } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Icon } from "../../components/Icon";
import { Kbd } from "../../components/Kbd";
import { TextField } from "../../components/TextField";
import { parseHuf } from "../../format";
import { POSITIVE_HINT } from "./answers";

interface Props {
  explanations: string[];
  pending: boolean;
  error: unknown;
  fieldError: string | undefined;
  onSubmit: (expected: number) => void;
}

/** Figma 10 Too little data (10:852), AC6: no estimate, ask for the expected monthly savings. */
export function TooLittleDataView({ explanations, pending, error, fieldError, onSubmit }: Props) {
  const [text, setText] = useState("");
  const [invalid, setInvalid] = useState(false);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const amount = parseHuf(text);
    if (amount === null || amount === 0) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    onSubmit(amount);
  }

  return (
    <form
      className="space-y-6 rounded-lg border border-border bg-surface p-8"
      onSubmit={submit}
      noValidate
    >
      <span className="flex size-12 items-center justify-center rounded-full bg-warning-bg text-warning">
        <Icon name="history" />
      </span>
      <h1 className="text-h1">We need a little more data</h1>
      {explanations.map((text) => (
        <p key={text} role="status" className="text-text-muted">
          {text}
        </p>
      ))}
      <TextField
        label="Expected monthly savings"
        inputMode="numeric"
        suffix="HUF"
        value={text}
        error={invalid ? POSITIVE_HINT : fieldError}
        onChange={(e) => setText(e.target.value)}
      />
      <ErrorMessage error={error} />
      <div className="flex items-center justify-end gap-3">
        <span className="text-caption text-text-muted">
          or press <Kbd>Enter ↵</Kbd>
        </span>
        <Button type="submit" disabled={pending}>
          Show my plan
        </Button>
      </div>
    </form>
  );
}
