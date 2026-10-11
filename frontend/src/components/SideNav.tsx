import { NavLink } from "react-router";
import type { Me } from "../api/types";
import { displayName } from "../format";
import { Badge } from "./Badge";
import { Icon, type IconName } from "./Icon";

const ITEMS: { to: string; label: string; icon: IconName; end: boolean }[] = [
  { to: "/", label: "Home", icon: "home", end: true },
  { to: "/plan", label: "Savings plan", icon: "savings", end: false },
  { to: "/activity", label: "Activity", icon: "activity", end: false },
];

/** Figma SideNav (frame 3:3), 248 px. Profile is omitted (no Figma frame, plan deviation). */
export function SideNav({
  user,
  onLogout,
  onNavigate,
}: {
  user: Me;
  onLogout: () => void;
  onNavigate?: () => void;
}) {
  const name = displayName(user.username);
  return (
    <div className="flex h-full w-sidebar flex-col border-r border-border bg-surface p-4">
      <p className="flex items-center gap-2 px-2 py-3 text-h3">
        <span
          aria-hidden="true"
          className="flex size-8 items-center justify-center rounded-md bg-primary text-on-primary"
        >
          S
        </span>
        SaverAI
      </p>
      <nav aria-label="Main" className="mt-4">
        <ul className="space-y-1">
          {ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                onClick={onNavigate}
                className={({ isActive }) =>
                  `flex min-h-touch items-center gap-3 rounded-md px-3 text-body outline-none focus-visible:shadow-focus ${isActive ? "bg-primary-subtle font-semibold text-primary" : "text-text-muted hover:bg-surface-hover"}`
                }
              >
                <Icon name={item.icon} />
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className="mt-auto space-y-3">
        <Badge tone="success">Simulated bank data</Badge>
        <div className="flex items-center gap-3 px-2">
          <span
            aria-hidden="true"
            className="flex size-8 items-center justify-center rounded-full bg-primary-subtle text-primary"
          >
            {name.charAt(0)}
          </span>
          <div>
            <p className="text-body font-semibold">{name}</p>
            <p className="text-caption text-text-muted">
              {user.role === "admin" ? "Admin" : "Customer"}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onLogout}
          className="flex min-h-touch w-full items-center gap-3 rounded-md px-3 text-body font-semibold text-primary outline-none hover:bg-primary-subtle focus-visible:shadow-focus"
        >
          <Icon name="log-out" />
          Log out
        </button>
      </div>
    </div>
  );
}
