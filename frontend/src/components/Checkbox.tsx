import type { InputHTMLAttributes } from "react";

/** Figma Checkbox (frame 2:182): the whole row is the 44 px target. */
export function Checkbox({
  label,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex min-h-touch cursor-pointer items-center gap-3 rounded-md px-3 hover:bg-surface-hover">
      <input
        type="checkbox"
        className="size-5 accent-primary outline-none focus-visible:shadow-focus"
        {...props}
      />
      <span className="text-body">{label}</span>
    </label>
  );
}
