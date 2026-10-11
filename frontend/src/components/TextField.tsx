import { useId, type InputHTMLAttributes } from "react";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string | null;
  suffix?: string;
}

/** Figma Input (frame 2:182): label, 44 px input, optional suffix ("HUF"), error then hint. */
export function TextField({
  label,
  hint,
  error,
  suffix,
  className = "",
  id,
  ...props
}: TextFieldProps) {
  const generated = useId();
  const inputId = id ?? generated;
  const errorId = `${inputId}-error`;
  const hintId = `${inputId}-hint`;
  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(" ");
  return (
    <div className={className}>
      <label htmlFor={inputId} className="block text-body font-semibold">
        {label}
      </label>
      <div className="relative mt-2">
        <input
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy || undefined}
          className={`block min-h-touch w-full rounded-md border bg-surface px-3 text-body text-text outline-none focus-visible:shadow-focus ${error ? "border-danger" : "border-border hover:border-border-strong"} ${suffix ? "pr-12" : ""}`}
          {...props}
        />
        {suffix ? (
          <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-caption text-text-muted">
            {suffix}
          </span>
        ) : null}
      </div>
      {error ? (
        <p id={errorId} className="mt-1 text-caption text-danger">
          {error}
        </p>
      ) : null}
      {hint ? (
        <p id={hintId} className="mt-1 text-caption text-text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
