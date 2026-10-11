import { useEffect, useId, useRef, type KeyboardEvent, type ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

const FOCUSABLE = 'input, button, a[href], select, textarea, [tabindex]:not([tabindex="-1"])';

/** Figma Modal (frame 2:236, 07b): centred, scrim 50 %, focus trapped, Esc closes. */
export function Modal({
  title,
  icon,
  onClose,
  children,
}: {
  title: string;
  icon?: IconName;
  onClose: () => void;
  children: ReactNode;
}) {
  const titleId = useId();
  const dialog = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const first =
      dialog.current?.querySelector<HTMLElement>("input") ??
      dialog.current?.querySelector<HTMLElement>(FOCUSABLE);
    first?.focus();
    return () => opener?.focus();
  }, []);

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.stopPropagation();
      onClose();
      return;
    }
    if (event.key !== "Tab" || dialog.current === null) return;
    const items = [...dialog.current.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
      (el) => !el.hasAttribute("disabled"),
    );
    const first = items[0];
    const last = items[items.length - 1];
    if (first === undefined || last === undefined) return;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div aria-hidden="true" className="absolute inset-0 bg-text/50" onClick={onClose} />
      <div
        ref={dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onKeyDown={onKeyDown}
        className="relative w-full max-w-120 rounded-lg bg-surface p-6 shadow-panel"
      >
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 id={titleId} className="flex items-center gap-3 text-h2">
            {icon ? (
              <span className="flex size-10 items-center justify-center rounded-full bg-primary-subtle text-primary">
                <Icon name={icon} />
              </span>
            ) : null}
            {title}
          </h2>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="flex size-touch items-center justify-center rounded-md outline-none hover:bg-surface-hover focus-visible:shadow-focus"
          >
            <Icon name="close" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
