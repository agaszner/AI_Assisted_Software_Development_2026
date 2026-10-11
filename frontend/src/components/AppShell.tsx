import { useEffect, useState, type ReactNode } from "react";
import type { Me } from "../api/types";
import { Icon } from "./Icon";
import { SideNav } from "./SideNav";

/** Sidebar layout (Figma 02, 08). Below 1024 px: top bar + drawer (Figma 10:906). */
export function AppShell({
  user,
  onLogout,
  children,
}: {
  user: Me;
  onLogout: () => void;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", close);
    return () => document.removeEventListener("keydown", close);
  }, [open]);

  return (
    <div className="min-h-screen lg:flex">
      <aside className="sticky top-0 hidden h-screen lg:block">
        <SideNav user={user} onLogout={onLogout} />
      </aside>
      <header className="flex h-14 items-center justify-between border-b border-border bg-surface px-4 lg:hidden">
        <p className="text-h3">SaverAI</p>
        <button
          type="button"
          aria-label="Open menu"
          aria-expanded={open}
          aria-controls="drawer"
          onClick={() => setOpen((value) => !value)}
          className="flex size-touch items-center justify-center rounded-md outline-none hover:bg-surface-hover focus-visible:shadow-focus"
        >
          <Icon name="menu" />
        </button>
      </header>
      {open ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-text/50"
            onClick={() => setOpen(false)}
          />
          <div id="drawer" className="relative h-full w-sidebar">
            <SideNav user={user} onLogout={onLogout} onNavigate={() => setOpen(false)} />
          </div>
        </div>
      ) : null}
      <main className="mx-auto w-full max-w-content flex-1 px-4 py-8 lg:px-8">{children}</main>
    </div>
  );
}
