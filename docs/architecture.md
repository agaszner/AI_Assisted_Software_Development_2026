# Architecture

## Components
- `backend/rules/` — pure rule engine (no Django): surplus (AC1, AC5), confidence (AC6), plan
  allocation (AC2, AC3), time machine (AC4), mandate check.
- `backend/banking/` — simulated bank: accounts, transactions, product catalogue, synthetic data.
- `backend/plans/` — questionnaire, plans, mandates, recurring orders, executions, audit log,
  explanation templates, services.
- `backend/api/` — Django Ninja JSON API (session login, input validation, ownership checks).
- `backend/core/clock.py` — injected time source.
- Django admin — Admin role: products and `RuleConfig`.

Dependency direction: `api` → `plans` / `banking` → `rules`. `banking` never imports `plans`.

## Data model
| Model | Purpose | Key constraints |
| --- | --- | --- |
| `banking.Account` | One simulated current account per customer, `balance` in HUF | OneToOne customer |
| `banking.Transaction` | Booked income (+) / expense (−); `own_transfer` excluded from surplus | — |
| `banking.Product` | Catalogue: risk 1–5, minimum horizon, liquid, active | check risk 1–5, unique code |
| `plans.RuleConfig` | Rule parameters, singleton, defaults from `rules/defaults.py` | pk = 1 |
| `plans.QuestionnaireAnswer` / `ExpenseAnswer` | Fixed questionnaire answers and planned expenses | — |
| `plans.Plan` | Proposal snapshot: amount, medians, confidence, status proposed/accepted/rejected/paused | — |
| `plans.PlanItem` | Ordered allocation lines with product | unique (plan, position) |
| `plans.Mandate` | Signed limits, versioned per customer | unique (customer, version), OneToOne plan |
| `plans.RecurringOrder` | One per accepted plan item | OneToOne plan item (AC7) |
| `plans.Execution` | One monthly run of one order, with mandate version and clause | unique idempotency key (AC7) |
| `plans.LogEntry` | Audit log; execution entries carry mandate version and clause | — |

All money fields are `BigIntegerField` (whole forints). Timestamps come from the injected clock.

## Main flow
questionnaire → `propose_plan` (rule engine) → plan review + time machine → accept (mandate vN,
recurring orders) → `manage.py run_orders` each month → `check_action` → execution + log entry.

## UI design
Figma file: https://www.figma.com/design/QUT5rnXj1U6BYjty7YH5uS (responsive web: 1440 px desktop frames,
375 px checks for Home and Plan review). The earlier top-navigation version,
https://www.figma.com/design/BqX09Awt7irGNkgUDShfsa, is kept for reference (AI usage case 3).
- Navigation: left sidebar `SideNav` (Home · Savings plan · Activity · Profile). The plan flow
  (questionnaire, spending analysis, plan review with its time machine sub-view, mandate) hides the
  sidebar and uses `FlowHeader` (Step N of 4, Back, Save & exit).
- Screens `01 Login` … `10 Too little data`, plus `05b`, `07b` and the 375 px frames, map to
  `frontend/src/screens/`. The `Components` board holds Icon/*, Button, Badge, Checkbox, RiskOption,
  Input, Tooltip, NavItem, SideNav, FlowHeader, StatTile, TransactionRow, PlanItem, LogRow and
  SummaryPanel, with hover and focus states for the interactive ones.
- Local variables (`color`, `space` collections), text styles and effect styles (`Focus/Ring`,
  `Elevation/*`) are the source for `frontend/src/theme/` tokens.
- Customer-facing texts are copied from `backend/plans/explanations.py` and the validation messages in
  `backend/plans/services.py`. Breakpoints and keyboard behaviour are on the
  `Responsive & interaction notes` frame.
