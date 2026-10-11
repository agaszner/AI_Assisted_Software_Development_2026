import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

/** Figma Buttons (frame 2:71): Primary, Secondary, Ghost, Danger × Default/Hover/Focus/Disabled. */
const VARIANTS: Record<Variant, string> = {
  primary: "bg-primary text-on-primary hover:bg-primary-hover",
  secondary: "border border-border bg-surface text-text hover:bg-surface-hover",
  ghost: "text-primary hover:bg-primary-subtle",
  danger: "bg-danger-bg text-danger hover:bg-surface-hover",
};

/** Classes for a button-looking element; use on `Link` too, so links get the 44 px target. */
export function buttonClass(variant: Variant = "primary"): string {
  return `inline-flex min-h-touch min-w-touch items-center justify-center gap-2 rounded-md px-4 text-body font-semibold outline-none focus-visible:shadow-focus disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]}`;
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

/** 44 px minimum target (AGENTS.md section 7). Give it visible text or an aria-label. */
export function Button({
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  return <button type={type} className={`${buttonClass(variant)} ${className}`} {...props} />;
}
