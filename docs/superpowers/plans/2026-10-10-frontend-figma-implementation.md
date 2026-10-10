# SaverAI Frontend from Figma (M2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Supersedes** `docs/superpowers/plans/2026-10-06-frontend-implementation.md` (written before the Figma file existed: mobile tab bar, hand-written tokens). Task 1 marks the old plan as superseded. Where a task below says "same as before", the full code is still repeated here: an executor reads only their own task.

> **Commits:** the user commits. Every task ends with a *suggested* Conventional Commit message. Do not run `git commit`, `git tag` or `git push` unless the user says so.

**Goal:** Build the M2 frontend of SaverAI as designed in Figma file `QUT5rnXj1U6BYjty7YH5uS` ("SaverAI Web", responsive web banking): screens 01 Login, 02 Home, 03 Questionnaire, 04 Spending analysis, 05/05b Plan review, 06 Time machine, 07/07b Mandate with password confirmation, 08 Active plan with execution log, 09 No surplus, 10 Too little data, plus the 375 px and 768–1023 px behaviour, and one Playwright e2e of the main workflow. Add the backend fields and endpoints the design needs, so the frontend computes nothing.

**Architecture:** `frontend/` is a Vite + React + TypeScript (strict) SPA. It talks only to the Django Ninja API through one fetch wrapper (`src/api/client.ts`) and TanStack Query hooks (`src/api/hooks.ts`). The Vite dev server proxies `/api` to `localhost:8000` (same-origin session and CSRF cookies). Layout: `AppShell` (left `SideNav`, a drawer below 1024 px) for Home / Savings plan / Activity, and `FlowLayout` (`FlowHeader`: Step N of 4, Back, Save & exit) for the plan flow. Every amount, date, percentage, product, confidence, explanation and audit text comes from the API; the frontend only formats and parses. Backend Tasks 2–5 add the missing read fields, password-confirmed signing, plan revision (mandate v2) and an activity feed.

**Tech Stack:** Node 22, npm, Vite 8, React 19, TypeScript 6.0 (strict), React Router 8, TanStack Query 5, Recharts 3, Tailwind CSS 4 (`@tailwindcss/vite`, Figma variables in `@theme`), `@fontsource-variable/inter`, Vitest 5 + jsdom + Testing Library, Playwright 1.63, ESLint 10 + typescript-eslint, Prettier 3. Backend: Django 5, Django Ninja (unchanged stack).

**Spec:** `docs/specification.md` (AC1–AC8). Design: Figma `https://www.figma.com/design/QUT5rnXj1U6BYjty7YH5uS` (frame ids in each task; read the `Responsive & interaction notes` frame `10:1074`). Also read `AGENTS.md`, `docs/architecture.md` ("UI design"), `docs/decisions/0002-backend-rule-interpretations.md`. If code and spec disagree, the spec wins: stop and flag it.

## Prerequisites and order

- The backend plan (`docs/superpowers/plans/2026-10-06-backend-implementation.md`, Tasks 1–14) is done: `make check` is green with 129 tests on 2026-10-10.
- Run tasks in order. Backend Tasks 2–5 fix the API contract that frontend Tasks 6–17 consume. Frontend screen tasks append to shared files (`src/api/hooks.ts`, `src/api/types.ts`, routes in `src/App.tsx`).
- Screen tests stub `fetch`, so Tasks 6–17 need no running backend. Task 18 (e2e) needs everything.
- Run commands from the repository root unless a step says `cd frontend` or `cd backend`.
- To look at a design frame while implementing, use the Figma MCP `get_screenshot` with `fileKey=QUT5rnXj1U6BYjty7YH5uS` and the frame id named in the task. Copy layout and texts; never copy the example numbers into code.

## Global Constraints

- No AI at runtime: no LLM SDK, model call or AI dependency in `frontend/` or `backend/`.
- The frontend computes no money, date, percentage or rule decision. It formats values (`formatHuf`, `formatMonth`, `formatDay`) and parses customer input (`parseHuf`). No `+`, `-`, `*`, `/`, `reduce` or `Math.*` on money in `frontend/src`; counts and progress come from the API.
- Money is a whole number of forints (`Huf = number`, integer). Never send a float or a numeric string; the backend answers 422 for `100.0`, `"100"`, `true`.
- Explanation texts (`explanations[]`, `median_explanation`, time machine `note`, activity `title`, rule `lines`, error `detail`) render exactly as sent. No client-side templates for rule results. Fixed UI copy (headings, button labels, Figma helper text without numbers) is fine.
- No `new Date()` / `Date.now()` in `frontend/src` (enforced by `src/theme/tokens.test.ts`). "Today" comes from `GET /api/account` (`today`), which honours `SAVERAI_FIXED_DATE`. Dates are shown by slicing ISO strings.
- TypeScript `strict`, no `any`, no non-null assertions.
- Colours, spacing, radii, shadows and type only from tokens in `src/theme/theme.css`, copied from the Figma variables (Task 7). Tailwind's default palette is disabled (`--color-*: initial`). No hex colours and no arbitrary values (`p-[13px]`) in `src/**/*.tsx` (enforced by `tokens.test.ts`).
- Every interactive element: at least 44 × 44 px target (`min-h-touch`), an accessible name, a hover state and the Figma focus ring (`focus-visible:shadow-focus`). Playwright checks heights (Task 18).
- Breakpoints from the Figma notes: `lg` = 1024 px (sidebar, two columns, sticky 360 px summary panel), `md` = 768 px. Below 1024 px the sidebar is a drawer behind a menu button and the summary panel is a sticky bottom action bar. Below 768 px one column, 16 px gutters, no horizontal scroll; the execution log becomes stacked rows.
- Dev server port **5173** (`strictPort`), because `CSRF_TRUSTED_ORIGINS` is `http://localhost:5173`.
- AC test names: `test_acN_<behaviour>` as the Vitest / Playwright title, so `make docs-check` finds them.
- Backend: rules stay pure (no Django in `backend/rules/`), `Clock` injected, templates in `plans/explanations.py`, rule parameters from `RuleConfig`, new migrations only (never edit `0001_initial.py`).
- No dependency beyond ADR-0003. Never edit or delete a failing test to make it pass; the one deliberate contract change (accept needs a password, Task 4) is recorded in ADR-0004, the commit message and `docs/ai-usage.md`.
- Every task updates `CHANGELOG.md` (`## [Unreleased]`), and `docs/traceability.md` if it adds an AC test (AGENTS.md section 8). Tick finished items in `docs/tasks.md`.

## Review Focus

Spec-silent inputs most likely to hurt a real user. Each has a pinned test in the owning task.

1. **Wrong password in the signing modal** → 403 "Incorrect password.", the modal stays open with the message, no orders and no mandate are created; a second try with the right password signs once (Task 4: `test_ac7_wrong_password_signs_nothing`; Task 16: `test("a wrong password keeps the modal open and shows the message")`).
2. **Double click on "Confirm and sign", or Enter pressed twice** → exactly one request (Task 16: `test_ac7_confirm_button_is_disabled_while_signing`).
3. **Amount typed as a decimal, with a sign, as text or empty** (`100.5`, `-5`, `1e5`, `abc`, `""`) → a field error and no request; `250 000` and `250,000` give 250000 (Task 7: `parseHuf`; Task 11: `test("a negative expense amount shows a field error without calling the API")`).
4. **Session expires mid-flow** (any call answers 401) → back to login, not an error page (Task 9: `test("an expired session mid-flow returns to login")`).
5. **Revising while a revision is already pending, or revising to an amount above the rule-engine amount** → 409 / 422 with the backend message, the active plan keeps running (Task 4: `test_revising_twice_is_a_conflict`, `test_revision_above_proposed_amount_is_rejected`; Task 17: `test("a revision error is shown in the change-amount modal")`).

## Interpretations, deviations and deferrals

Recorded in ADR-0004 (Task 4) and here. The user approves them by approving this plan.

- **Figma numbers are illustrative.** 735,000 HUF / 2 skipped months, 1,220,000 HUF balance etc. are not produced by the seed data (anna has 6 months: 441,000 HUF, no skipped month). Tests use fixtures; the e2e asserts only seed-derived values (73,500 HUF).
- **Password-confirmed signing (07b, chosen by the user):** `POST /api/plans/{id}/accept` takes `{"password": "..."}` and checks it with `user.check_password`; wrong → 403 `Incorrect password.`, nothing created. Simulated strong customer authentication. The idempotency of AC7 is unchanged (a second accept with the password returns 200, no duplicates). Existing API tests that call accept get the password in the body: this is the contract change, not a loosened test.
- **Change amount of an active plan (08, full Figma parity, chosen by the user):** `POST /api/plans/{id}/revise {"monthly_amount": n}` on an accepted plan creates a new *proposed* plan (`revises` = old plan) from the same questionnaire and analysis, amount between 1 and the old plan's `proposed_amount`. Nothing changes until the revision is signed: accepting it pauses the old plan, its mandate and orders (§4) and signs mandate version N+1 in one transaction. Rejecting the revision leaves the old plan running. Only one pending revision per plan (409). **Interpretation, flagged for the author:** the spec says "Customer rejects or lowers the amount: nothing executes until a revised plan is accepted". This plan reads it as "nothing of the *revised* plan executes before signing" and keeps the old plan running meanwhile (so an abandoned revision does not silently stop saving). The stricter reading (pause the old plan as soon as a revision is proposed) changes `revise_plan` and its tests; switch before Task 4 if the author prefers it. Figma text: "Changing the amount creates mandate version 2; version 1 stays in the log". New migration: `Plan.revises`.
- **Next transfer date** = first day of the month after today (`rules.months.next_transfer_on`), because `run_orders` is meant to run on the 1st. A manual `run_orders` in the current month can still execute earlier (demo use).
- **Saved so far per plan item (Home progress bars):** backend sum of executed transfers of all the customer's orders with the same item kind and label, plus the questionnaire's existing emergency fund for the emergency-fund item; `progress_percent` = floor(saved × 100 / target), capped at 100, computed in the backend. `None` when the item has no target.
- **Planned-expense due date** comes from the questionnaire expense with the item's label (item labels are expense names). Two expenses with the same name share the first due date (`ponytail:` comment).
- **Activity feed (`GET /api/activity`)** for the execution log on 08 and the Activity page: scheduled rows (next period of each active order that has no execution yet), executions (with audit fields) and plan events. Titles are templates in `plans/explanations.py`. `LogEntry` gains a nullable `amount` (new migration) so event rows show the amount at the time.
- **Rule summary on Home** ("How the plan is calculated") comes from `GET /api/rules` (templates filled from `RuleConfig`), never hard-coded.
- **Spending analysis (04):** `GET /api/analysis` gains `share_percent`, `median_explanation` ("Sorted: … Median = …", a template filled with the rule result) and `explanations`. The Figma tooltip remark "One-off high month. The median ignores it." is dropped: it is a judgement the rule engine does not make. The tooltip shows month and value only.
- **Field-level questionnaire errors:** `InvalidInput` carries an optional `field` (`"planned_expenses.1.due_on"`), returned as `{"detail": ..., "field": ...}`. The frontend shows it under that field, otherwise above the Continue button. No client-side past-date check (it would disagree with `SAVERAI_FIXED_DATE`).
- **09 No surplus and 10 Too little data** render inside the questionnaire route (`/questionnaire`), so the answers stay in component state for the "expected monthly savings" resubmission. A reload returns to an empty questionnaire.
- **Flow URLs:** step 1 `/questionnaire`, step 2 `/plans/:planId/analysis`, step 3 `/plans/:planId` with sub-view `/plans/:planId/time-machine`, step 4 `/plans/:planId/mandate`. "Save & exit" goes to Home (no draft storage). "Back" goes one step back.
- **SideNav:** Home `/`, Savings plan `/plan`, Activity `/activity` (the execution log on its own page). **Profile is omitted**: the Figma file has no Profile frame and no AC needs it. Greeting: "Hello, Anna" (the username capitalised); "Good morning" would need the time of day on the client.
- **05b "Transfer waiting for your approval"** appears on 08 / Activity once `run_orders` created the waiting execution (with an Approve button); plan review shows the low-confidence notice from `explanations`.
- **No "resume paused plan"**, no Profile, no "View all" transactions page (Home shows the 5 newest; the link is omitted).
- **Icons:** inline SVG paths in `src/components/Icon.tsx` (20 px, 1.75 stroke, same names as the Figma `Icon/*` set). No icon library.
- **Font:** Inter via `@fontsource-variable/inter` (works offline at the defence), system font fallback.
- **Admin role** keeps using Django admin at `http://localhost:8000/admin/`.
- **`make e2e` resets the local database** (flush, migrate, seed) so the flow can run repeatedly.

## File map

```
Makefile, README.md, AGENTS.md (sections 3, 4)          Task 1, 18
CHANGELOG.md, docs/tasks.md                             every task
scripts/docs_check.py                                   Task 1
docs/decisions/0003-frontend-stack.md                   Task 1
docs/decisions/0004-signing-and-revision.md             Task 4
docs/superpowers/plans/2026-10-06-frontend-implementation.md   Task 1 (superseded note)
docs/traceability.md                                    Tasks 2, 4, 12–18
docs/architecture.md                                    Tasks 4, 5, 18
docs/manual-checks.md, docs/ai-usage.md                 Task 18
backend/rules/months.py                                 Task 3   next_transfer_on
backend/plans/explanations.py                           Tasks 2, 3, 5   rule lines, median working, activity titles
backend/plans/services.py                               Tasks 3, 4, 5   InvalidInput.field, saved amounts, revise, log amounts
backend/plans/models.py + migrations 0002, 0003         Tasks 4, 5   Plan.revises, LogEntry.amount
backend/plans/activity.py                               Task 5   activity rows
backend/api/schemas.py, backend/api/routes.py, api.py   Tasks 2–5
backend/tests/api/test_frontend_endpoints.py            Task 2
backend/tests/api/test_plan_details_api.py              Task 3
backend/tests/services/test_revision.py, tests/api/test_signing_api.py   Task 4
backend/tests/api/test_activity_api.py                  Task 5
frontend/ config files                                  Task 1, 18 (playwright.config.ts)
frontend/src/api/{types,client,queryClient,hooks}.ts    Task 6, then hooks/types grow per screen
frontend/src/test/{setup.ts,render.tsx,fixtures.ts}     Task 6, 9
frontend/src/format.ts                                  Task 7
frontend/src/theme/theme.css, tokens.test.ts            Task 1 (import), Task 7
frontend/src/components/                                Task 7 (Icon, Button, Badge, TextField, MoneyField, Checkbox, ErrorMessage, Card, StatTile)
                                                        Task 8 (SideNav, AppShell, FlowHeader, FlowLayout, SummaryPanel, Modal)
                                                        Task 10 (TransactionRow), Task 14 (PlanItemCard, SavedChart), Task 17 (ExecutionLog)
frontend/src/screens/login/                             Task 9   01
frontend/src/screens/home/                              Task 10  02
frontend/src/screens/questionnaire/                     Tasks 11, 12   03, 09, 10
frontend/src/screens/analysis/                          Task 13  04
frontend/src/screens/plan-review/                       Task 14  05, 05b
frontend/src/screens/time-machine/                      Task 15  06
frontend/src/screens/mandate/                           Task 16  07, 07b
frontend/src/screens/active-plan/, screens/activity/    Task 17  08
frontend/e2e/                                           Task 18
```

Every screen and component file has a `*.test.tsx` next to it or in `components/components.test.tsx`.

---

### Task 1: Frontend skeleton, tooling, Makefile, ADR-0003, docs-check for frontend tests

Deliverable: `make lint`, `make test-fe` and `make docs-check` are green on a Vite + React skeleton. This task verifies the toolchain versions that later tasks rely on.

**Files:**
- Create: `frontend/package.json`, `frontend/index.html`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/eslint.config.js`, `frontend/.prettierrc.json`, `frontend/.prettierignore`
- Create: `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `frontend/src/test/setup.ts`, `frontend/src/theme/theme.css`
- Create: `docs/decisions/0003-frontend-stack.md`
- Modify: `Makefile`, `scripts/docs_check.py`, `README.md`, `AGENTS.md` (sections 3 and 4), `CHANGELOG.md`, `docs/superpowers/plans/2026-10-06-frontend-implementation.md` (superseded note)

**Interfaces:**
- Consumes: `scripts/docs_check.py` and `Makefile` from backend plan Tasks 1–2.
- Produces: npm scripts `dev`, `build`, `test`, `lint`, `fmt`, `e2e`; Make targets `dev-backend`, `dev-frontend`, `test-fe`, `e2e`; `App` component exported from `src/App.tsx`; Vitest setup file `src/test/setup.ts`.

- [ ] **Step 1: Write ADR-0003 (dependency approval record)**

Create `docs/decisions/0003-frontend-stack.md`:

```markdown
# 0003. Frontend tech stack and dependencies
Date: 2026-10-10 · Status: proposed

## Context
AGENTS.md section 3 fixes React + TypeScript (strict) + Vite, Tailwind CSS, TanStack Query and
Recharts. ADR-0001 deferred the frontend dependencies to the frontend plan. This ADR lists every
frontend dependency so none is added silently.

## Decision
- Node 22 or newer, **npm** with a committed `frontend/package-lock.json`.
- Runtime: **react** and **react-dom** 19, **react-router** 8 (one URL per screen: back button,
  reload and Playwright deep links work), **@tanstack/react-query** 5 (server state, cache
  invalidation after accept / pause), **recharts** 3 (spending analysis and time machine charts),
  **@fontsource-variable/inter** (the Figma typeface, bundled so the app works offline).
- Build: **vite** 8, **@vitejs/plugin-react**, **typescript ~6.0** (typescript-eslint supports
  TypeScript < 6.1, so TypeScript 7 is not used yet), **tailwindcss** 4 with **@tailwindcss/vite**
  (design tokens in `src/theme/theme.css` `@theme`, copied from the Figma variables of file
  `QUT5rnXj1U6BYjty7YH5uS`; the default palette is disabled).
- Tests: **vitest** 5, **jsdom**, **@testing-library/react**, **@testing-library/user-event**,
  **@testing-library/jest-dom**, **@playwright/test** (Chromium only).
- Quality: **eslint** 10, **@eslint/js**, **typescript-eslint**, **eslint-plugin-react-hooks**,
  **globals**, **prettier**; types **@types/react**, **@types/react-dom**, **@types/node**.
- No AI / LLM dependency (AGENTS.md golden rule 1).
- Not added: MSW (tests stub `fetch`), axios (`fetch` is enough), form libraries, date libraries
  (ISO date strings are sliced), global state libraries (TanStack Query holds server state),
  icon libraries (the 16 Figma icons are inline SVG paths), dialog / headless-UI libraries (one
  small `Modal` component).

## Alternatives considered
- A `useState` screen switch instead of a router: no deep links, no back button, harder e2e.
- MSW for API mocks: one more dependency for what a 25-line `fetch` stub does.
- Tailwind 3 with `tailwind.config.js`: Tailwind 4 keeps the tokens in CSS, one file.
- TypeScript 7: not yet supported by typescript-eslint.
- Inter from Google Fonts: an external request at runtime, fails offline at the defence.

## Consequences
- The Vite dev server proxies `/api` to `localhost:8000`, so session and CSRF cookies are
  same-origin. The port is fixed at 5173 because `CSRF_TRUSTED_ORIGINS` names it.
- `make setup` needs Node 22 and downloads Chromium for Playwright.
- AGENTS.md section 3 lists React Router.
```

- [ ] **Step 2: Create the npm project files**

`frontend/package.json`:

```json
{
  "name": "saverai-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "engines": {
    "node": ">=22"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc -p tsconfig.json && vite build",
    "test": "vitest run",
    "lint": "eslint . && tsc -p tsconfig.json && prettier --check .",
    "fmt": "prettier --write . && eslint --fix .",
    "e2e": "playwright test"
  },
  "dependencies": {
    "@fontsource-variable/inter": "^5.2.8",
    "@tanstack/react-query": "^5.104.1",
    "react": "^19.3.0",
    "react-dom": "^19.3.0",
    "react-router": "^8.4.0",
    "recharts": "^3.10.1"
  },
  "devDependencies": {
    "@eslint/js": "^10.0.1",
    "@playwright/test": "^1.63.0",
    "@tailwindcss/vite": "^4.3.3",
    "@testing-library/jest-dom": "^7.0.1",
    "@testing-library/react": "^16.3.3",
    "@testing-library/user-event": "^14.6.7",
    "@types/node": "^24.19.1",
    "@types/react": "^19.3.0",
    "@types/react-dom": "^19.3.0",
    "@vitejs/plugin-react": "^6.1.2",
    "eslint": "^10.12.0",
    "eslint-plugin-react-hooks": "^7.1.1",
    "globals": "^17.13.0",
    "jsdom": "^30.1.2",
    "prettier": "^3.9.9",
    "tailwindcss": "^4.3.3",
    "typescript": "~6.0.3",
    "typescript-eslint": "^8.71.1",
    "vite": "^8.3.3",
    "vitest": "^5.0.3"
  }
}
```

`frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SaverAI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "noEmit": true,
    "types": ["vite/client", "node"]
  },
  "include": ["src", "e2e", "vite.config.ts", "playwright.config.ts", "eslint.config.js"]
}
```

`frontend/vite.config.ts`:

```ts
/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // The backend's CSRF_TRUSTED_ORIGINS names this exact origin.
    port: 5173,
    strictPort: true,
    // Same-origin API calls: the session and CSRF cookies just work.
    proxy: { "/api": "http://localhost:8000" },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
```

`frontend/eslint.config.js`:

```js
import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "playwright-report", "test-results"] },
  js.configs.recommended,
  ...tseslint.configs.strict,
  reactHooks.configs.flat.recommended,
  {
    languageOptions: { globals: globals.browser },
    rules: { "@typescript-eslint/no-explicit-any": "error" },
  },
);
```

`frontend/.prettierrc.json`:

```json
{ "printWidth": 100 }
```

`frontend/.prettierignore`:

```
dist
playwright-report
test-results
package-lock.json
```

`frontend/src/theme/theme.css` (Task 7 adds the Figma tokens):

```css
@import "tailwindcss";
```

`frontend/src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
```

- [ ] **Step 3: Install and write the failing smoke test**

Run: `cd frontend && npm install`
Expected: `package-lock.json` is created, `found 0 vulnerabilities` (warnings about funding are fine).

`frontend/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { App } from "./App";

test("renders the app name", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "SaverAI" })).toBeInTheDocument();
});
```

- [ ] **Step 4: Run it to verify it fails**

Run: `cd frontend && npx vitest run`
Expected: FAIL with `Failed to resolve import "./App"`.

- [ ] **Step 5: Implement the skeleton app**

`frontend/src/App.tsx`:

```tsx
/** Placeholder; Task 9 replaces it with the router. */
export function App() {
  return <h1>SaverAI</h1>;
}
```

`frontend/src/main.tsx`:

```tsx
import "./theme/theme.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

- [ ] **Step 6: Run tests and lint**

Run: `cd frontend && npx vitest run && npm run fmt && npm run lint && npm run build`
Expected: `1 passed`; ESLint, `tsc` and Prettier clean; Vite build succeeds. If `tsc` reports an unknown option or ESLint fails to load `tseslint.config`, check the installed versions against `package.json` before changing config.

- [ ] **Step 7: Makefile targets**

In `Makefile`, replace the `.PHONY` line and the `setup`, `dev`, `lint`, `fmt` and `check` targets, and add `dev-backend`, `dev-frontend`, `test-fe` and `e2e`. Keep `migrate`, `seed`, `test` and `docs-check` as they are. Recipe lines start with a TAB.

```make
.PHONY: setup migrate seed dev dev-backend dev-frontend test test-fe e2e lint fmt docs-check check

setup:
	test -f .env || cp .env.example .env
	cd backend && uv sync
	cd frontend && npm ci && npx playwright install chromium

dev:
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uv run python manage.py runserver 8000

dev-frontend:
	cd frontend && npm run dev

test-fe:
	cd frontend && npm test

# Starts both servers if they are not running. Resets the local database (flush, migrate, seed).
e2e:
	cd frontend && npx playwright test

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy .
	cd frontend && npm run lint

fmt:
	cd backend && uv run ruff check --fix . && uv run ruff format .
	cd frontend && npm run fmt

check: lint test test-fe docs-check
```

- [ ] **Step 8: Teach docs-check frontend test references**

In `scripts/docs_check.py`, add below `TEST_REF`:

```python
FRONTEND_REF = re.compile(r"frontend/[\w/.-]+\.(?:test|spec)\.tsx?(?:::\w+)?")
```

Replace `test_reference_exists` with:

```python
def test_reference_exists(ref: str) -> bool:
    """Backend refs are relative to backend/ and name a `def`; frontend refs are relative to the
    repository root and name a quoted Vitest / Playwright test title."""
    path, _, name = ref.partition("::")
    in_frontend = path.startswith("frontend/")
    file = (ROOT if in_frontend else BACKEND) / path
    if not file.is_file():
        return False
    if not name:
        return True
    if in_frontend:
        pattern = rf"""["']{re.escape(name)}["']"""
    else:
        pattern = rf"^\s*def {re.escape(name)}\("
    return re.search(pattern, file.read_text(), re.MULTILINE) is not None
```

In `main()`, change the reference loop to check both kinds:

```python
        for ref in TEST_REF.findall(evidence) + FRONTEND_REF.findall(evidence):
```

Add one line to the module docstring: `- frontend references (frontend/...test.tsx::title) must name an existing file and test title.`

- [ ] **Step 9: Verify docs-check catches a missing frontend test**

Temporarily append `; frontend/src/App.test.tsx::test_ac1_missing` to the AC1 evidence cell in `docs/traceability.md` (AC1 is `passing`). Run `make docs-check`.
Expected: exit 1 with `docs-check: AC1: referenced test not found: frontend/src/App.test.tsx::test_ac1_missing`.
Remove the temporary text (and restore the status if you changed it). Run `make docs-check` again.
Expected: `docs-check: OK`.

- [ ] **Step 10: README, AGENTS.md, CHANGELOG**

In `README.md`, change the Requirements list to:

```markdown
## Requirements
- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- Node.js 22 or newer (npm)
```

and the setup block to:

```markdown
## Setup and run
    make setup      # backend + frontend deps, Playwright Chromium, .env from .env.example
    make migrate    # create the SQLite database
    make dev        # backend on http://localhost:8000, app on http://localhost:5173
```

and add under Quality:

```markdown
    make test-fe    # frontend tests (Vitest)
    make e2e        # Playwright end-to-end tests; RESETS the local database (flush, migrate, seed)
```

In `AGENTS.md` section 3, change the Frontend row to:

```markdown
| Frontend | React + TypeScript (strict) + Vite, React Router, Tailwind CSS, TanStack Query, Recharts (ADR-0003) |
```

In `AGENTS.md` section 4, change the e2e line to:

```bash
make e2e          # Playwright end-to-end tests (starts servers if needed; resets the local database)
```

Add to `CHANGELOG.md` under `### Added`:

```markdown
- React + TypeScript + Vite frontend skeleton with Vitest, ESLint, Prettier; `make dev` runs backend and frontend, new `make test-fe` and `make e2e` (ADR-0003).
- `make docs-check` also verifies frontend test references in `docs/traceability.md`.
```

Add at the top of `docs/superpowers/plans/2026-10-06-frontend-implementation.md`, below the title:

```markdown
> **Superseded** by `docs/superpowers/plans/2026-10-10-frontend-figma-implementation.md` (based on the
> Figma file `QUT5rnXj1U6BYjty7YH5uS`). Kept for reference; do not execute.
```

Tick in `docs/tasks.md`: "React + TypeScript (strict) + Vite + Tailwind in `frontend/`." and "Tooling config: ruff, mypy, pytest, pytest-django, Hypothesis, eslint, prettier, Vitest." (backend tooling exists already). Leave the `Makefile` item until Task 18 adds `e2e` and it runs.

- [ ] **Step 11: Full check**

Run: `make fmt && make check`
Expected: backend lint and 129 tests green, `1 passed` from Vitest, `docs-check: OK`.

- [ ] **Step 12: Suggested commit (user commits)**

`feat(frontend): vite react typescript skeleton and tooling (ADR-0003)`

---
### Task 2: Backend read endpoints for Home and Mandate (account, mandate, rules)

Deliverable: `GET /api/account` (with the server's `today`), `GET /api/plans/{id}/mandate` and `GET /api/rules`, with ownership checks. No data model change. Figma frames: `5:118` (02 Home), `8:422` (07 Mandate).

**Files:**
- Modify: `backend/api/schemas.py`, `backend/api/routes.py`, `backend/plans/explanations.py`
- Create: `backend/tests/api/test_frontend_endpoints.py`
- Modify: `backend/tests/services/test_explanations.py`
- Modify: `docs/traceability.md` (AC8 row), `README.md` (API paragraph), `CHANGELOG.md`

**Interfaces:**
- Consumes (existing backend): `current_user` (`api/auth.py`), `get_clock` (`core/clock.py`), `Account`, `Transaction`, `Product` (`banking/models.py`), `Mandate`, `RuleConfig` (`plans/models.py`; `RuleConfig.load() -> RuleParams`), `Plan.per_transfer_approval`, `rules.mandate.CLAUSES: dict[int, str]`, `owned_plan`, `plan_out` (`api/routes.py`), `explanations.huf`, `create_catalogue`, `create_customer(username, surpluses, *, balance=1_000_000)` (password `pw`) (`tests/factories.py`), `AC1_SERIES`, `TODAY = date(2026, 10, 6)` (`tests/constants.py`; `conftest.py` pins `SAVERAI_FIXED_DATE` to it)
- Produces:

| Method | Path | Response |
| --- | --- | --- |
| GET | `/api/account` | `AccountOut {today: date, name, balance, min_balance, transactions: TransactionOut[]}` (5 newest up to today); 404 when the user has no account |
| GET | `/api/plans/{id}/mandate` | `MandateOut {status: "unsigned"\|"active"\|"paused", version: int (unsigned: the version that signing creates, Figma 07 "Mandate · version 1"), signed_at: datetime\|null, max_monthly_amount, min_balance, per_transfer_approval, products: ProductOut[], clauses: ClauseOut[]}`; 403 another customer's plan |

| GET | `/api/rules` | `RulesOut {lines: string[]}`: the four plan rules filled from `RuleConfig` |

`TransactionOut {id, booked_on, amount, description, own_transfer}`, `ClauseOut {number, text}`. Also `api.routes.product_out(product: Product) -> ProductOut` and `explanations.rule_lines(params: RuleParams) -> list[str]`.

- [ ] **Step 1: Write the failing tests**

`backend/tests/api/test_frontend_endpoints.py`:

```python
from datetime import timedelta
from typing import Any

import pytest
from django.contrib.auth.models import User
from django.test import Client

from banking.models import Account, Product, Transaction
from plans.models import RuleConfig
from rules.mandate import CLAUSES
from tests.constants import AC1_SERIES, TODAY
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

QUESTIONNAIRE: dict[str, Any] = {
    "risk_score": 3,
    "existing_emergency_fund": 750_000,
    "planned_expenses": [],
}


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def proposed_plan_id(client: Client) -> int:
    assert post(client, "/api/questionnaire", QUESTIONNAIRE).status_code == 201
    plan_id: int = post(client, "/api/plans").json()["plan"]["id"]
    return plan_id


def test_account_requires_login(client: Client) -> None:
    assert client.get("/api/account").status_code == 401


def test_account_shows_today_balance_minimum_and_five_newest_transactions(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES, balance=600_000))
    body = client.get("/api/account").json()
    assert (body["today"], body["balance"], body["min_balance"]) == (TODAY.isoformat(), 600_000, 100_000)
    dates = [t["booked_on"] for t in body["transactions"]]
    assert len(dates) == 5
    assert dates == sorted(dates, reverse=True)
    assert {"own_transfer", "description"} <= set(body["transactions"][0])


def test_account_hides_transactions_after_today(client: Client) -> None:
    user = create_customer("anna", AC1_SERIES)
    Transaction.objects.create(
        account=Account.objects.get(customer=user),
        booked_on=TODAY + timedelta(days=1),
        amount=-1,
        description="Future",
    )
    client.force_login(user)
    descriptions = [t["description"] for t in client.get("/api/account").json()["transactions"]]
    assert "Future" not in descriptions


def test_user_without_account_gets_404(client: Client) -> None:
    client.force_login(User.objects.create_user(username="nobody", password="pw"))
    assert client.get("/api/account").status_code == 404


def test_mandate_preview_matches_signed_mandate(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES))
    plan_id = proposed_plan_id(client)

    preview = client.get(f"/api/plans/{plan_id}/mandate").json()
    assert (preview["status"], preview["version"], preview["signed_at"]) == ("unsigned", 1, None)
    assert (preview["max_monthly_amount"], preview["min_balance"]) == (73_500, 100_000)
    assert [c["number"] for c in preview["clauses"]] == sorted(CLAUSES)
    assert preview["products"]

    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 200
    signed = client.get(f"/api/plans/{plan_id}/mandate").json()
    assert (signed["status"], signed["version"]) == ("active", 1)
    assert signed["signed_at"] is not None
    for key in ("version", "max_monthly_amount", "min_balance", "per_transfer_approval", "products", "clauses"):
        assert signed[key] == preview[key], key


def test_rules_follow_rule_config(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES))
    lines = client.get("/api/rules").json()["lines"]
    assert lines[0] == "Monthly amount = 70% of your median monthly surplus (last 6 months)."
    assert lines[3] == "A transfer is skipped if it would leave less than 100,000 HUF on your account."
    config = RuleConfig.objects.get_or_create(pk=1)[0]
    config.monthly_share_percent = 60
    config.save()
    assert client.get("/api/rules").json()["lines"][0].startswith("Monthly amount = 60%")


def test_ac8_other_customer_cannot_view_mandate(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES))
    plan_id = proposed_plan_id(client)
    client.logout()
    client.force_login(create_customer("bob", AC1_SERIES))
    assert client.get(f"/api/plans/{plan_id}/mandate").status_code == 403
```

`test_mandate_preview_matches_signed_mandate` pins the one risk of this task: the preview is built in the route, the signed mandate in `services.accept_plan`. If someone changes one side, this test fails.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/api/test_frontend_endpoints.py`
Expected: FAIL — `/api/account`, `/api/rules` and `/api/plans/{id}/mandate` return 404 (routes do not exist).

- [ ] **Step 3: Add the schemas**

In `backend/api/schemas.py`, change the date import to `from datetime import date, datetime` and append:

```python
class TransactionOut(Schema):
    id: int
    booked_on: date
    amount: int
    description: str
    own_transfer: bool


class AccountOut(Schema):
    today: date  # the server's Clock (honours SAVERAI_FIXED_DATE); the UI never reads its own clock
    name: str
    balance: int
    min_balance: int
    transactions: list[TransactionOut]


class RulesOut(Schema):
    lines: list[str]


class ClauseOut(Schema):
    number: int
    text: str


class MandateOut(Schema):
    status: str  # "unsigned" (plan only proposed), "active" or "paused"
    version: int  # unsigned: the version that accepting will sign
    signed_at: datetime | None
    max_monthly_amount: int
    min_balance: int
    per_transfer_approval: bool
    products: list[ProductOut]
    clauses: list[ClauseOut]
```

- [ ] **Step 4: Add the routes**

In `backend/api/routes.py`:

1. Add the imports (`make fmt` sorts them): `from banking.models import Account, Product`, `from django.db.models import Max` and `from rules.mandate import CLAUSES`; add `Mandate` to the existing `from plans.models import ...` line (it already imports `RuleConfig`); add `AccountOut`, `ClauseOut`, `MandateOut`, `RulesOut`, `TransactionOut` to the `api.schemas` import list.

2. Add a module constant below `router = Router(...)`:

```python
# Display limit for the home screen (Figma 02 shows five), not a rule parameter.
RECENT_TRANSACTIONS = 5
```

3. Add `product_out` above `plan_out` and use it inside `plan_out` (replace the inline `ProductOut(...)` with `product=product_out(item.product)`):

```python
def product_out(product: Product) -> ProductOut:
    return ProductOut(
        id=product.pk, name=product.name, risk_level=product.risk_level, liquid=product.liquid
    )
```

4. Append the endpoints at the end of the file:

```python
@router.get("/account", response=AccountOut)
def get_account(request: HttpRequest) -> AccountOut:
    """Balance and the newest transactions up to today (home screen)."""
    account = Account.objects.filter(customer=current_user(request)).first()
    if account is None:
        raise Http404("No account found.")
    today = get_clock().today()
    rows = account.transactions.filter(booked_on__lte=today).order_by("-booked_on", "-id")[
        :RECENT_TRANSACTIONS
    ]
    return AccountOut(
        today=today,
        name=account.name,
        balance=account.balance,
        min_balance=RuleConfig.load().min_balance,
        transactions=[
            TransactionOut(
                id=t.pk,
                booked_on=t.booked_on,
                amount=t.amount,
                description=t.description,
                own_transfer=t.own_transfer,
            )
            for t in rows
        ],
    )


@router.get("/rules", response=RulesOut)
def get_rules(request: HttpRequest) -> RulesOut:
    """The plan rules in words, filled from RuleConfig (Home: "How the plan is calculated")."""
    return RulesOut(lines=explanations.rule_lines(RuleConfig.load()))


@router.get("/plans/{plan_id}/mandate", response=MandateOut)
def get_mandate(request: HttpRequest, plan_id: int) -> MandateOut:
    """The signed mandate of an accepted plan, or a preview of the terms that accepting signs."""
    plan = owned_plan(request, plan_id)
    clauses = [ClauseOut(number=number, text=text) for number, text in sorted(CLAUSES.items())]
    signed = Mandate.objects.filter(plan=plan).first()
    if signed is not None:
        return MandateOut(
            status=signed.status,
            version=signed.version,
            signed_at=signed.signed_at,
            max_monthly_amount=signed.max_monthly_amount,
            min_balance=signed.min_balance,
            per_transfer_approval=signed.per_transfer_approval,
            products=[product_out(p) for p in signed.products.order_by("risk_level", "id")],
            clauses=clauses,
        )
    # Same terms as services.accept_plan signs (pinned by test_mandate_preview_matches_signed_mandate).
    products = {item.product.pk: item.product for item in plan.items.select_related("product")}
    latest = Mandate.objects.filter(customer_id=plan.customer_id).aggregate(v=Max("version"))["v"]
    return MandateOut(
        status="unsigned",
        version=(latest or 0) + 1,  # same rule as services.accept_plan
        signed_at=None,
        max_monthly_amount=plan.monthly_amount,
        min_balance=RuleConfig.load().min_balance,
        per_transfer_approval=plan.per_transfer_approval,
        products=[
            product_out(p) for p in sorted(products.values(), key=lambda p: (p.risk_level, p.pk))
        ],
        clauses=clauses,
    )
```

- [ ] **Step 4b: Add the rule-lines template (test first)**

Append to `backend/tests/services/test_explanations.py`:

```python
def test_rule_lines_are_filled_from_parameters() -> None:
    from rules.defaults import DEFAULTS

    assert explanations.rule_lines(DEFAULTS) == [
        "Monthly amount = 70% of your median monthly surplus (last 6 months).",
        "Priority: emergency fund (3× median monthly expenses), then planned expenses, then "
        "long-term investment.",
        "Money needed within 12 months goes only to low-risk, liquid products.",
        "A transfer is skipped if it would leave less than 100,000 HUF on your account.",
    ]
```

Run: `cd backend && uv run pytest tests/services/test_explanations.py -k rule_lines` — Expected: FAIL (`no attribute 'rule_lines'`).

In `backend/plans/explanations.py`, add `from rules.defaults import RuleParams` to the imports and append:

```python
RULE_LINES = (
    "Monthly amount = {percent}% of your median monthly surplus (last {window} months).",
    "Priority: emergency fund ({fund_months}× median monthly expenses), then planned expenses, "
    "then long-term investment.",
    "Money needed within {liquid_months} months goes only to low-risk, liquid products.",
    "A transfer is skipped if it would leave less than {minimum} HUF on your account.",
)


def rule_lines(params: RuleParams) -> list[str]:
    values = {
        "percent": params.monthly_share_percent,
        "window": params.surplus_window_months,
        "fund_months": params.emergency_fund_months,
        "liquid_months": params.liquid_horizon_months,
        "minimum": huf(params.min_balance),
    }
    return [line.format(**values) for line in RULE_LINES]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/api tests/services/test_explanations.py -v`
Expected: all pass, including the 7 new endpoint tests, the new template test and the unchanged `test_plans_api.py`.

- [ ] **Step 6: Docs and check**

In `docs/traceability.md`, append to the AC8 evidence cell: `; tests/api/test_frontend_endpoints.py::test_ac8_other_customer_cannot_view_mandate`.

In `README.md`, extend the API paragraph's endpoint list with: `account (today, balance, minimum balance, recent transactions), rules (plan rules in words), plan mandate (terms and clauses)`.

Add to `CHANGELOG.md` under `### Added`:

```markdown
- API: `GET /api/account` (server date, balance, minimum balance, 5 newest transactions), `GET /api/rules` (plan rules filled from `RuleConfig`) and `GET /api/plans/{id}/mandate` (mandate terms and clauses, preview before acceptance); another customer's mandate returns 403 (AC8).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 7: Suggested commit (user commits)**

`feat(api): account, rules and mandate read endpoints for the frontend (AC8)`

---

### Task 3: Backend plan, analysis and time machine details for the Figma screens

Deliverable: every value that Figma 02, 04, 05, 06 and 08 show is in the API: plan meta (date, risk score, share, minimum balance, next transfer, mandate version, saved total), per-item due date and progress, the analysis working text and explanations, time machine counts, and field-level questionnaire errors. No data model change.

**Files:**
- Modify: `backend/rules/money.py`, `backend/rules/months.py`, `backend/plans/explanations.py`, `backend/plans/services.py`, `backend/api/api.py`, `backend/api/schemas.py`, `backend/api/routes.py`
- Modify: `backend/tests/rules/test_money.py`, `backend/tests/services/test_explanations.py`
- Create: `backend/tests/api/test_plan_details_api.py`
- Modify: `docs/traceability.md` (AC8 row), `CHANGELOG.md`

**Interfaces:**
- Consumes: `median`, `percent_of` (`rules/money.py`), `month_of`, `add_months` (`rules/months.py`), `ItemKind` (`rules/plan.py`), `services.analyse(customer, clock) -> tuple[SurplusAnalysis, Confidence]`, `explanations.no_surplus(months, median)`, `explanations.needs_expected_savings(months, required)`, `explanations.huf`, `Execution`, `Mandate`, `RuleConfig`, `ExpenseAnswer` (related name: check `plans/models.py`; the code below uses `questionnaire.expenses`), the `clock` fixture (`tests/conftest.py`, a `FixedClock` on `TODAY`), `run_monthly_orders(clock)`.
- Produces (pure): `rules.money.middle_values(values: Sequence[Huf]) -> tuple[Huf, ...]` (one or two middle values of the sorted input), `rules.money.progress_percent(saved: Huf, target: Huf) -> int` (floor, capped at 100), `rules.months.next_transfer_on(today: date) -> date`.
- Produces (templates): `explanations.median_working(values: Sequence[Huf], median: Huf) -> str`.
- Produces (services): `services.item_saved_amounts(plan: Plan) -> dict[int, Huf]` (by `PlanItem.pk`), `services.plan_saved_total(plan: Plan) -> Huf`, `InvalidInput(message, field=None)` with attribute `field: str | None`.
- Produces (API, additive):

| Schema | New fields |
| --- | --- |
| `PlanOut` | `created_on: date`, `median_surplus: int \| None`, `months_of_data: int`, `share_percent: int`, `risk_score: int`, `min_balance: int`, `next_transfer_on: date`, `mandate_version: int \| None`, `signed_on: date \| None`, `saved_total: int` |
| `PlanItemOut` | `position: int`, `due_on: date \| None`, `saved_amount: int`, `progress_percent: int \| None` |
| `AnalysisOut` | `share_percent: int`, `median_explanation: str \| None`, `explanations: list[str]` |
| `TimeMachineOut` | `months_replayed: int`, `transfers_made: int` |
| 422 body of `InvalidInput` | `{"detail": str, "field": str}` when a field is known |

- [ ] **Step 1: Write the failing pure tests**

Append to `backend/tests/rules/test_money.py` (add `middle_values, progress_percent` to the `rules.money` import and `next_transfer_on` to the `rules.months` import):

```python
def test_middle_values_for_odd_and_even_counts() -> None:
    assert middle_values([300_000, 80_000, 100_000, 120_000, 90_000, 110_000]) == (100_000, 110_000)
    assert middle_values([3, 1, 2]) == (2,)


def test_progress_percent_rounds_down_and_caps_at_100() -> None:
    assert progress_percent(720_000, 750_000) == 96
    assert progress_percent(0, 300_000) == 0
    assert progress_percent(900_000, 750_000) == 100


def test_next_transfer_is_the_first_of_next_month() -> None:
    assert next_transfer_on(date(2026, 10, 8)) == date(2026, 11, 1)
    assert next_transfer_on(date(2026, 12, 31)) == date(2027, 1, 1)
```

Append to `backend/tests/services/test_explanations.py`:

```python
def test_median_working_shows_the_sorted_values_and_the_middle() -> None:
    assert explanations.median_working(
        [100_000, 120_000, 80_000, 110_000, 90_000, 300_000], 105_000
    ) == (
        "Sorted: 80,000 · 90,000 · 100,000 · 110,000 · 120,000 · 300,000. "
        "Median = (100,000 + 110,000) / 2 = 105,000 HUF."
    )
    assert explanations.median_working([3, 1, 2], 2) == "Sorted: 1 · 2 · 3. Median = 2 HUF."
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd backend && uv run pytest tests/rules/test_money.py tests/services/test_explanations.py`
Expected: FAIL with `ImportError: cannot import name 'middle_values'` (and `no attribute 'median_working'`).

- [ ] **Step 3: Implement the pure helpers and the template**

Append to `backend/rules/money.py`:

```python
def middle_values(values: Sequence[Huf]) -> tuple[Huf, ...]:
    """The value(s) `median` uses: one for an odd count, two for an even count."""
    if not values:
        raise ValueError("middle values of an empty sequence")
    ordered = sorted(values)
    middle = len(ordered) // 2
    return (ordered[middle],) if len(ordered) % 2 else (ordered[middle - 1], ordered[middle])


def progress_percent(saved: Huf, target: Huf) -> int:
    """Whole percent of `target` reached, rounded down, at most 100. `target` must be positive."""
    return min(100, saved * 100 // target)
```

Append to `backend/rules/months.py`:

```python
def next_transfer_on(today: date) -> date:
    """Recurring orders run on the 1st, so the next transfer is the first of next month."""
    return add_months(month_of(today), 1)
```

In `backend/plans/explanations.py`, add `from collections.abc import Sequence` and `from rules.money import middle_values` (next to the existing `Huf` import), then append:

```python
MEDIAN_EVEN = "Sorted: {values}. Median = ({low} + {high}) / 2 = {median} HUF."
MEDIAN_ODD = "Sorted: {values}. Median = {median} HUF."


def median_working(values: Sequence[Huf], median: Huf) -> str:
    """How the rule engine's median follows from the monthly surpluses (04 Spending analysis)."""
    listed = " · ".join(huf(v) for v in sorted(values))
    middle = middle_values(values)
    if len(middle) == 1:
        return MEDIAN_ODD.format(values=listed, median=huf(median))
    return MEDIAN_EVEN.format(
        values=listed, low=huf(middle[0]), high=huf(middle[1]), median=huf(median)
    )
```

Run the Step 2 command again. Expected: PASS. Run `cd backend && uv run pytest tests/rules/test_purity.py` too: `rules/` still imports nothing forbidden.

- [ ] **Step 4: Write the failing API tests**

`backend/tests/api/test_plan_details_api.py`:

```python
from typing import Any

import pytest
from django.test import Client

from banking.models import Product
from core.clock import FixedClock
from plans.execution import run_monthly_orders
from tests.constants import AC1_SERIES, TODAY
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

ANSWERS: dict[str, Any] = {
    "risk_score": 2,
    "existing_emergency_fund": 720_000,
    "planned_expenses": [{"name": "New laptop", "amount": 300_000, "due_on": "2027-08-01"}],
}


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def proposed(client: Client, answers: dict[str, Any] = ANSWERS) -> dict[str, Any]:
    client.force_login(create_customer("anna", AC1_SERIES))
    assert post(client, "/api/questionnaire", answers).status_code == 201
    plan: dict[str, Any] = post(client, "/api/plans").json()["plan"]
    return plan


def test_plan_shows_the_values_of_the_review_screen(client: Client) -> None:
    plan = proposed(client)
    assert plan["created_on"] == TODAY.isoformat()
    assert (plan["median_surplus"], plan["months_of_data"], plan["share_percent"]) == (105_000, 6, 70)
    assert (plan["risk_score"], plan["min_balance"]) == (2, 100_000)
    assert plan["next_transfer_on"] == "2026-11-01"
    assert (plan["mandate_version"], plan["signed_on"], plan["saved_total"]) == (None, None, 0)


def test_items_show_position_due_date_and_progress(client: Client) -> None:
    items = proposed(client)["items"]
    assert [i["position"] for i in items] == list(range(len(items)))
    fund, laptop = items[0], items[1]
    assert fund["kind"] == "emergency_fund"
    assert fund["saved_amount"] == 720_000  # the fund the customer already has
    assert fund["progress_percent"] == min(100, 720_000 * 100 // fund["target_amount"])
    assert (laptop["label"], laptop["due_on"]) == ("New laptop", "2027-08-01")
    assert (laptop["saved_amount"], laptop["progress_percent"]) == (0, 0)


def test_executed_transfers_count_as_saved(client: Client, clock: FixedClock) -> None:
    plan = proposed(client)
    assert post(client, f"/api/plans/{plan['id']}/accept").status_code == 200
    run_monthly_orders(clock)
    after = client.get(f"/api/plans/{plan['id']}").json()
    assert (after["mandate_version"], after["signed_on"]) == (1, TODAY.isoformat())
    assert after["saved_total"] == plan["monthly_amount"]
    fund = after["items"][0]
    assert fund["saved_amount"] == 720_000 + fund["monthly_amount"]


def test_analysis_explains_the_median(client: Client) -> None:
    proposed(client)
    body = client.get("/api/analysis").json()
    assert body["share_percent"] == 70
    assert body["median_explanation"].endswith("Median = (100,000 + 110,000) / 2 = 105,000 HUF.")
    assert body["explanations"] == []


def test_ac5_analysis_explains_no_surplus(client: Client) -> None:
    client.force_login(create_customer("bence", [-40_000] * 6))
    body = client.get("/api/analysis").json()
    assert body["explanations"] and "no surplus" in body["explanations"][0]


def test_ac6_analysis_asks_for_expected_savings(client: Client) -> None:
    client.force_login(create_customer("csilla", [50_000, 60_000]))
    body = client.get("/api/analysis").json()
    assert body["median_explanation"] is None
    assert "expect to save" in body["explanations"][0]


def test_time_machine_counts_transfers(client: Client) -> None:
    plan = proposed(client)
    body = client.get(f"/api/plans/{plan['id']}/time-machine").json()
    assert body["months_replayed"] == len(body["months"])
    assert body["transfers_made"] == sum(1 for m in body["months"] if not m["skipped"])


def test_ac8_past_expense_date_names_the_field(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES))
    answers = {
        **ANSWERS,
        "planned_expenses": [
            {"name": "New laptop", "amount": 300_000, "due_on": "2027-08-01"},
            {"name": "Holiday", "amount": 50_000, "due_on": "2026-09-01"},
        ],
    }
    response = post(client, "/api/questionnaire", answers)
    assert response.status_code == 422
    assert response.json() == {
        "detail": "The due date of 'Holiday' (2026-09-01) is in the past.",
        "field": "planned_expenses.1.due_on",
    }
```

- [ ] **Step 5: Run them to verify they fail**

Run: `cd backend && uv run pytest tests/api/test_plan_details_api.py`
Expected: FAIL with `KeyError: 'created_on'` and similar missing keys.

- [ ] **Step 6: Field-level `InvalidInput`**

In `backend/plans/services.py`, replace the `InvalidInput` class:

```python
class InvalidInput(Exception):
    """Well-formed input that breaks a business rule (HTTP 422). `field` names the input, e.g.
    "planned_expenses.1.due_on", so the UI can show the message next to it."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
```

In `submit_questionnaire`, change the loop and the two checks below it to pass the field:

```python
    for index, expense in enumerate(planned_expenses):
        if expense.amount <= 0:
            raise InvalidInput(
                f"The amount of '{expense.name}' must be positive.",
                f"planned_expenses.{index}.amount",
            )
        if expense.due_on < today:
            raise InvalidInput(
                f"The due date of '{expense.name}' ({expense.due_on}) is in the past.",
                f"planned_expenses.{index}.due_on",
            )
    if existing_emergency_fund < 0:
        raise InvalidInput(
            "The existing emergency fund cannot be negative.", "existing_emergency_fund"
        )
    if expected_monthly_savings is not None and expected_monthly_savings <= 0:
        raise InvalidInput(
            "The expected monthly savings must be positive.", "expected_monthly_savings"
        )
```

In `backend/api/api.py`, replace the `invalid_input` handler body:

```python
@api.exception_handler(InvalidInput)
def invalid_input(request: HttpRequest, exc: InvalidInput) -> HttpResponse:
    body = {"detail": str(exc)}
    if exc.field is not None:
        body["field"] = exc.field
    return api.create_response(request, body, status=422)
```

- [ ] **Step 7: Saved amounts in the plan service**

Append to `backend/plans/services.py` (change `from django.db.models import Max` to `from django.db.models import Max, Sum`, add `Execution` to the `plans.models` import and `ItemKind` to the `rules.plan` import):

```python
def item_saved_amounts(plan: Plan) -> dict[int, Huf]:
    """Saved so far per plan item (by PlanItem pk): executed transfers of all the customer's
    orders with the same item kind and label, so a revised plan continues the same pot. The
    emergency fund also counts the fund the customer already had (questionnaire)."""
    rows = (
        Execution.objects.filter(
            order__mandate__customer_id=plan.customer_id, status=Execution.Status.EXECUTED
        )
        .values("order__plan_item__kind", "order__plan_item__label")
        .annotate(total=Sum("amount"))
    )
    executed = {(r["order__plan_item__kind"], r["order__plan_item__label"]): r["total"] for r in rows}
    # ponytail: a later questionnaire that already includes SaverAI transfers in its emergency
    # fund counts them twice; track pots per customer if questionnaires are re-taken often.
    existing = plan.questionnaire.existing_emergency_fund
    return {
        item.pk: executed.get((item.kind, item.label), 0)
        + (existing if item.kind == ItemKind.EMERGENCY_FUND else 0)
        for item in plan.items.all()
    }


def plan_saved_total(plan: Plan) -> Huf:
    """Executed transfers of this plan's orders ("Saved by SaverAI")."""
    total = Execution.objects.filter(
        order__plan_item__plan=plan, status=Execution.Status.EXECUTED
    ).aggregate(total=Sum("amount"))["total"]
    return total or 0
```

- [ ] **Step 8: Schemas**

In `backend/api/schemas.py`, change `PlanItemOut`, `PlanOut`, `AnalysisOut` and `TimeMachineOut` to:

```python
class PlanItemOut(Schema):
    position: int
    kind: str
    label: str
    product: ProductOut
    monthly_amount: int
    target_amount: int | None
    due_on: date | None  # planned expenses only
    saved_amount: int
    progress_percent: int | None  # None when the item has no target


class PlanOut(Schema):
    id: int
    status: str
    created_on: date
    monthly_amount: int
    proposed_amount: int
    median_surplus: int | None
    months_of_data: int
    share_percent: int
    risk_score: int
    min_balance: int
    confidence: str
    per_transfer_approval: bool
    next_transfer_on: date
    mandate_version: int | None
    signed_on: date | None
    saved_total: int
    items: list[PlanItemOut]
    explanations: list[str]
```

```python
class AnalysisOut(Schema):
    months_of_data: int
    confidence: str
    median_surplus: int | None
    median_expenses: int
    monthly_amount: int | None
    share_percent: int
    median_explanation: str | None
    explanations: list[str]  # no-surplus (AC5) or too-little-data (AC6) message, else empty
    months: list[MonthOut]
```

```python
class TimeMachineOut(Schema):
    total_saved: int
    months_replayed: int
    transfers_made: int
    skipped_months: list[date]
    months: list[BacktestMonthOut]
```

- [ ] **Step 9: Routes**

In `backend/api/routes.py`, add the imports `from rules.months import next_transfer_on` and `Mandate` to the `plans.models` import (Task 2 may have added it already). Replace `plan_out` with:

```python
def plan_out(plan: Plan) -> PlanOut:
    params = RuleConfig.load()
    mandate = Mandate.objects.filter(plan=plan).first()
    saved = services.item_saved_amounts(plan)
    # ponytail: two expenses with the same name share the first due date; store due_on on
    # PlanItem if that ever matters.
    due_dates: dict[str, date] = {}
    for expense in plan.questionnaire.expenses.order_by("due_on"):
        due_dates.setdefault(expense.name, expense.due_on)
    items = [
        PlanItemOut(
            position=item.position,
            kind=item.kind,
            label=item.label,
            product=product_out(item.product),
            monthly_amount=item.monthly_amount,
            target_amount=item.target_amount,
            due_on=due_dates.get(item.label) if item.kind == ItemKind.PLANNED_EXPENSE else None,
            saved_amount=saved[item.pk],
            progress_percent=(
                progress_percent(saved[item.pk], item.target_amount)
                if item.target_amount
                else None
            ),
        )
        for item in plan.items.select_related("product")
    ]
    return PlanOut(
        id=plan.pk,
        status=plan.status,
        created_on=plan.created_at.date(),
        monthly_amount=plan.monthly_amount,
        proposed_amount=plan.proposed_amount,
        median_surplus=plan.median_surplus,
        months_of_data=plan.months_of_data,
        share_percent=params.monthly_share_percent,
        risk_score=plan.questionnaire.risk_score,
        min_balance=mandate.min_balance if mandate else params.min_balance,
        confidence=plan.confidence,
        per_transfer_approval=plan.per_transfer_approval,
        next_transfer_on=next_transfer_on(get_clock().today()),
        mandate_version=mandate.version if mandate else None,
        signed_on=mandate.signed_at.date() if mandate else None,
        saved_total=services.plan_saved_total(plan),
        items=items,
        explanations=explanations.plan_summary(
            amount=plan.monthly_amount,
            median_surplus=plan.median_surplus,
            percent=params.monthly_share_percent,
            months_of_data=plan.months_of_data,
            confidence=Confidence(plan.confidence),
        ),
    )
```

Add the imports it needs: `from datetime import date`, `from rules.money import progress_percent`, `from rules.plan import ItemKind, Outcome, Proposal` (extend the existing line). If the expense related name is not `expenses`, check `ExpenseAnswer.questionnaire`'s `related_name` in `plans/models.py` and use that.

Replace the `analysis` route:

```python
@router.get("/analysis", response=AnalysisOut)
def analysis(request: HttpRequest) -> AnalysisOut:
    result, confidence = services.analyse(current_user(request), get_clock())
    params = RuleConfig.load()
    if result.median_surplus is None:
        notes = [explanations.needs_expected_savings(result.months_of_data, params.min_months_for_estimate)]
    elif result.median_surplus <= 0:  # AC5 boundary, ADR-0002
        notes = [explanations.no_surplus(len(result.flows), result.median_surplus)]
    else:
        notes = []
    return AnalysisOut(
        months_of_data=result.months_of_data,
        confidence=confidence.value,
        median_surplus=result.median_surplus,
        median_expenses=result.median_expenses,
        monthly_amount=result.monthly_amount,
        share_percent=params.monthly_share_percent,
        median_explanation=(
            None
            if result.median_surplus is None
            else explanations.median_working([f.surplus for f in result.flows], result.median_surplus)
        ),
        explanations=notes,
        months=[
            MonthOut(month=f.month, income=f.income, expenses=f.expenses, surplus=f.surplus)
            for f in result.flows
        ],
    )
```

In the `time_machine` route, add two arguments to `TimeMachineOut(...)`:

```python
        months_replayed=len(result.months),
        transfers_made=sum(1 for m in result.months if not m.skipped),
```

- [ ] **Step 10: Run all backend tests**

Run: `cd backend && uv run pytest`
Expected: all pass (129 existing + the new ones). If `test_ac5_analysis_explains_no_surplus` fails because the median of bence's months is not computed over `result.flows`, print `result.flows` and compare with `no_plan_explanations` in `api/routes.py`; both must use the same month count.

- [ ] **Step 11: Docs and check**

In `docs/traceability.md`, append to the AC8 evidence cell: `; tests/api/test_plan_details_api.py::test_ac8_past_expense_date_names_the_field`; to AC5: `; tests/api/test_plan_details_api.py::test_ac5_analysis_explains_no_surplus`; to AC6: `; tests/api/test_plan_details_api.py::test_ac6_analysis_asks_for_expected_savings`.

Add to `CHANGELOG.md` under `### Added`:

```markdown
- API details for the web UI: plan date, risk score, share, minimum balance, next transfer, mandate version and saved total; per-item due date and progress; spending-analysis median working and no-surplus / too-little-data explanations; time machine transfer counts (AC4–AC6).
- Questionnaire errors name the field (`{"detail", "field"}`), e.g. a past expense date (AC8).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 12: Suggested commit (user commits)**

`feat(api): plan, analysis and time machine details for the web ui (AC4-AC8)`

---

### Task 4: Password-confirmed signing and plan revision (mandate v2), ADR-0004

Deliverable: `POST /api/plans/{id}/accept` needs the customer's password (Figma `8:550`, 07b); `POST /api/plans/{id}/revise` proposes a new amount for an active plan, and signing the revision pauses the old plan and signs mandate version N+1 (Figma `8:708`, "Change amount"; 07 "Changing the amount creates mandate version 2; version 1 stays in the log"). One new migration.

**Files:**
- Create: `docs/decisions/0004-signing-and-revision.md`
- Modify: `backend/plans/models.py`; create the migration with `makemigrations` (`backend/plans/migrations/0002_plan_revises.py`)
- Modify: `backend/plans/services.py`, `backend/api/schemas.py`, `backend/api/routes.py`
- Create: `backend/tests/services/test_revision.py`, `backend/tests/api/test_signing_api.py`
- Modify (contract change, see Step 9): `backend/tests/api/test_plans_api.py`, `backend/tests/api/test_frontend_endpoints.py`, `backend/tests/api/test_plan_details_api.py`
- Modify: `docs/architecture.md` (data model), `docs/traceability.md` (AC7, AC8), `README.md` (API paragraph), `CHANGELOG.md`

**Interfaces:**
- Consumes: `services.accept_plan`, `pause_plan`, `edit_amount`, `reject_plan`, `active_plan`, `log_event`, `PlanConflict`, `InvalidInput(message, field)` (Task 3), `allocate`, `NoEligibleProduct` (`rules/plan.py`, already imported by services), `owned_plan`, `plan_out` (Task 3), `AmountIn`, test helpers `proposed_plan(clock, username="anna", fund=0)` pattern from `tests/services/test_acceptance.py`.
- Produces:
  - Model: `Plan.revises: Plan | None` (`related_name="revisions"`).
  - `services.revise_plan(plan: Plan, monthly_amount: Huf, clock: Clock) -> Plan` (the new proposed plan).
  - `accept_plan` signs a revision while the plan it revises is accepted, pausing that plan first.
  - API: `AcceptIn {password: str}`; `POST /api/plans/{id}/accept` body `AcceptIn` → `PlanOut`, 403 `Incorrect password.`; `POST /api/plans/{id}/revise` body `AmountIn` → `PlanOut` of the revision; `PlanOut.revises: int | None` (the plan this one would replace) and `PlanOut.pending_revision: int | None` (a proposed revision of this plan waiting for signature).

- [ ] **Step 1: Write ADR-0004**

Create `docs/decisions/0004-signing-and-revision.md`:

```markdown
# 0004. Password-confirmed signing and plan revision
Date: 2026-10-10 · Status: proposed

## Context
The Figma design (file QUT5rnXj1U6BYjty7YH5uS, frames 07b and 08) asks the customer to confirm the
mandate with their password and lets them change the amount of an active plan ("Changing the
amount creates mandate version 2; version 1 stays in the log"). The backend accepted a plan without
any confirmation and could edit only proposed plans. The specification says "Customer rejects or
lowers the amount: nothing executes until a revised plan is accepted"; this ADR interprets it as
"the revised amount does not execute before it is signed" (see Decision).

## Decision
- `POST /api/plans/{id}/accept` takes `{"password": "..."}`. The ownership check runs first (403
  for another customer's plan, AC8), then `user.check_password`; a wrong password answers 403
  `Incorrect password.` and creates nothing. Acceptance stays idempotent (AC7). Simulated strong
  customer authentication; no real bank.
- `POST /api/plans/{id}/revise {"monthly_amount": n}` on an accepted plan creates a new proposed
  plan with `revises` = the old plan, the same questionnaire and analysis, and an amount between 1
  and the old plan's rule-engine amount. Only one pending revision per plan (409).
- The old plan keeps running until the revision is signed (interpretation of the spec sentence
  above; the stricter reading is listed under Alternatives). Signing it pauses the old plan, its
  mandate and its orders (clause 4) and signs mandate version N+1, in one transaction. Rejecting
  the revision leaves the old plan running.
- New nullable field `Plan.revises` (migration 0002).

## Alternatives considered
- A confirm dialog without a password: no change to the API, but the Figma flow shows a password.
- A password field checked only in the browser: a fake security control; rejected.
- Editing the active plan in place: would change orders without a new signed mandate and lose the
  audit trail of version 1.
- Pausing the old plan when the revision is proposed: a customer who then abandons the revision
  would silently stop saving.

## Consequences
- API tests that accept a plan send the password (the test customers' password is `pw`).
- The login endpoint and the signing check have no rate limiting (demo scope; Django's defaults).
- `active_plan()` (newest accepted or paused plan) returns the signed revision after signing.
```

- [ ] **Step 2: Write the failing service tests**

`backend/tests/services/test_revision.py`:

```python
import pytest

from banking.models import Product
from core.clock import FixedClock
from plans.models import Mandate, Plan, RecurringOrder
from plans.services import (
    InvalidInput,
    PlanConflict,
    accept_plan,
    active_plan,
    propose_plan,
    reject_plan,
    revise_plan,
    submit_questionnaire,
)
from tests.constants import AC1_SERIES
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def accepted_plan(clock: FixedClock) -> Plan:
    customer = create_customer("anna", AC1_SERIES)
    submit_questionnaire(
        customer,
        risk_score=3,
        existing_emergency_fund=0,
        expected_monthly_savings=None,
        planned_expenses=(),
        clock=clock,
    )
    _, plan = propose_plan(customer, clock)
    assert plan is not None
    accept_plan(plan, clock)
    plan.refresh_from_db()
    return plan


def test_revision_keeps_the_active_plan_running_until_signed(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    revision = revise_plan(plan, 50_000, clock)
    plan.refresh_from_db()
    assert (revision.status, revision.revises_id, revision.monthly_amount) == ("proposed", plan.pk, 50_000)
    assert sum(item.monthly_amount for item in revision.items.all()) == 50_000
    assert plan.status == Plan.Status.ACCEPTED
    assert not RecurringOrder.objects.filter(plan_item__plan=plan, status="paused").exists()


def test_signing_a_revision_pauses_the_old_plan_and_signs_version_2(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    revision = revise_plan(plan, 50_000, clock)
    accept_plan(revision, clock)
    plan.refresh_from_db()
    assert plan.status == Plan.Status.PAUSED
    assert Mandate.objects.get(plan=plan).status == Mandate.Status.PAUSED
    assert set(RecurringOrder.objects.filter(plan_item__plan=plan).values_list("status", flat=True)) == {"paused"}
    assert Mandate.objects.get(plan=revision).version == 2
    assert active_plan(plan.customer) == revision


def test_ac7_signing_a_revision_twice_creates_orders_once(clock: FixedClock) -> None:
    revision = revise_plan(accepted_plan(clock), 50_000, clock)
    accept_plan(revision, clock)
    accept_plan(revision, clock)
    assert RecurringOrder.objects.filter(plan_item__plan=revision).count() == revision.items.count()


def test_rejecting_a_revision_leaves_the_plan_running(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    reject_plan(revise_plan(plan, 50_000, clock), clock)
    plan.refresh_from_db()
    assert plan.status == Plan.Status.ACCEPTED
    assert revise_plan(plan, 40_000, clock).status == Plan.Status.PROPOSED  # a new try is allowed


def test_revising_twice_is_a_conflict(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    revise_plan(plan, 50_000, clock)
    with pytest.raises(PlanConflict, match="already waiting"):
        revise_plan(plan, 40_000, clock)


def test_revision_above_proposed_amount_is_rejected(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    with pytest.raises(InvalidInput, match="between 1 and 73500"):
        revise_plan(plan, 73_501, clock)
    assert not Plan.objects.filter(revises=plan).exists()


def test_only_an_active_plan_can_be_revised(clock: FixedClock) -> None:
    plan = accepted_plan(clock)
    revision = revise_plan(plan, 50_000, clock)
    with pytest.raises(PlanConflict, match="Only an active plan"):
        revise_plan(revision, 40_000, clock)
```

- [ ] **Step 3: Run them to verify they fail**

Run: `cd backend && uv run pytest tests/services/test_revision.py`
Expected: FAIL with `ImportError: cannot import name 'revise_plan'`.

- [ ] **Step 4: Model field and migration**

In `backend/plans/models.py`, add to `Plan` below `created_at`:

```python
    revises = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="revisions",
        help_text="The accepted plan this proposal would replace when signed (ADR-0004).",
    )
```

Run: `cd backend && uv run python manage.py makemigrations plans --name plan_revises`
Expected: `plans/migrations/0002_plan_revises.py` with one `AddField`. Never edit `0001_initial.py`.

- [ ] **Step 5: Services**

In `backend/plans/services.py`, extract the allocation from `edit_amount` into a helper and use it there. Replace the whole `edit_amount` function with:

```python
def _allocate(plan: Plan, monthly_amount: Huf, clock: Clock) -> list[PlanItemDraft]:
    """Re-run the priority allocation for `plan`'s questionnaire with a new amount."""
    if not 0 < monthly_amount <= plan.proposed_amount:
        raise InvalidInput(
            f"The monthly amount must be between 1 and {plan.proposed_amount} HUF.",
            "monthly_amount",
        )
    answer = plan.questionnaire
    try:
        return list(
            allocate(
                monthly_amount,
                median_expenses=plan.median_expenses,
                risk_score=answer.risk_score,
                existing_emergency_fund=answer.existing_emergency_fund,
                planned_expenses=_expenses(answer),
                today=clock.today(),
                products=_active_products(),
                params=RuleConfig.load(),
            )
        )
    except NoEligibleProduct as error:
        raise PlanConflict(str(error)) from error


def edit_amount(plan: Plan, monthly_amount: Huf, clock: Clock) -> Plan:
    """Lower the amount of a proposed plan and re-run the allocation. Nothing executes until
    the revised plan is accepted."""
    plan.refresh_from_db()
    if plan.status != Plan.Status.PROPOSED:
        raise PlanConflict("Only a proposed plan can be edited.")
    items = _allocate(plan, monthly_amount, clock)
    with transaction.atomic():
        plan.items.all().delete()
        _save_items(plan, items)
        plan.monthly_amount = monthly_amount
        plan.save(update_fields=["monthly_amount"])
        log_event(
            plan.customer,
            "plan_edited",
            f"Plan {plan.pk} amount set to {monthly_amount} HUF a month.",
            clock,
            plan=plan,
        )
    return plan


def revise_plan(plan: Plan, monthly_amount: Huf, clock: Clock) -> Plan:
    """Propose a new amount for an accepted plan (ADR-0004). The accepted plan keeps running
    until the revision is signed; accept_plan then pauses it."""
    plan.refresh_from_db()
    if plan.status != Plan.Status.ACCEPTED:
        raise PlanConflict("Only an active plan can be revised.")
    if plan.revisions.filter(status=Plan.Status.PROPOSED).exists():
        raise PlanConflict("A revised plan is already waiting for your signature.")
    items = _allocate(plan, monthly_amount, clock)
    with transaction.atomic():
        revision = Plan.objects.create(
            customer_id=plan.customer_id,
            questionnaire=plan.questionnaire,
            revises=plan,
            monthly_amount=monthly_amount,
            proposed_amount=plan.proposed_amount,
            median_surplus=plan.median_surplus,
            median_expenses=plan.median_expenses,
            months_of_data=plan.months_of_data,
            confidence=plan.confidence,
            created_at=clock.now(),
        )
        _save_items(revision, items)
        log_event(
            plan.customer,
            "plan_revised",
            f"Plan {revision.pk} proposed to replace plan {plan.pk}: {monthly_amount} HUF a month.",
            clock,
            plan=revision,
        )
    return revision
```

Add `PlanItemDraft` to the `from rules.plan import (...)` list if it is not there.

In `accept_plan`, replace the two lines

```python
        if Plan.objects.filter(customer_id=plan.customer_id, status=Plan.Status.ACCEPTED).exists():
            raise PlanConflict("Pause your active plan before accepting a new one.")
```

with

```python
        active = (
            Plan.objects.select_for_update()
            .filter(customer_id=plan.customer_id, status=Plan.Status.ACCEPTED)
            .first()
        )
        if active is not None and active.pk != plan.revises_id:
            raise PlanConflict("Pause your active plan before accepting a new one.")
        if active is not None:  # signing a revision replaces the plan it revises (ADR-0004)
            pause_plan(active, clock)
```

`pause_plan` is defined below `accept_plan`; that is fine in Python (resolved at call time). Its own `transaction.atomic()` nests as a savepoint, so a failure later in `accept_plan` rolls the pause back too.

- [ ] **Step 6: Run the service tests**

Run: `cd backend && uv run pytest tests/services`
Expected: all pass, including the 7 new revision tests and the unchanged acceptance tests (`edit_amount` keeps its behaviour; its message is unchanged).

- [ ] **Step 7: Write the failing API tests**

`backend/tests/api/test_signing_api.py`:

```python
from typing import Any

import pytest
from django.test import Client

from banking.models import Product
from plans.models import Mandate, RecurringOrder
from tests.constants import AC1_SERIES
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

ANSWERS: dict[str, Any] = {"risk_score": 3, "existing_emergency_fund": 750_000, "planned_expenses": []}
SIGN = {"password": "pw"}  # tests.factories.create_customer's password


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def proposed_id(client: Client, username: str = "anna") -> int:
    client.force_login(create_customer(username, AC1_SERIES))
    assert post(client, "/api/questionnaire", ANSWERS).status_code == 201
    plan_id: int = post(client, "/api/plans").json()["plan"]["id"]
    return plan_id


def test_ac7_wrong_password_signs_nothing(client: Client) -> None:
    plan_id = proposed_id(client)
    response = post(client, f"/api/plans/{plan_id}/accept", {"password": "wrong"})
    assert (response.status_code, response.json()) == (403, {"detail": "Incorrect password."})
    assert not Mandate.objects.exists() and not RecurringOrder.objects.exists()
    assert client.get(f"/api/plans/{plan_id}").json()["status"] == "proposed"
    assert post(client, f"/api/plans/{plan_id}/accept", SIGN).json()["status"] == "accepted"
    assert post(client, f"/api/plans/{plan_id}/accept", SIGN).status_code == 200
    assert RecurringOrder.objects.count() == len(client.get(f"/api/plans/{plan_id}").json()["items"])


def test_accept_without_password_is_rejected(client: Client) -> None:
    plan_id = proposed_id(client)
    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 422


def test_ac8_own_password_cannot_sign_another_customers_plan(client: Client) -> None:
    plan_id = proposed_id(client)
    client.logout()
    client.force_login(create_customer("bob", AC1_SERIES))
    response = post(client, f"/api/plans/{plan_id}/accept", SIGN)
    assert response.status_code == 403
    assert response.json()["detail"] == "This plan belongs to another customer."


def test_revise_endpoint_returns_the_revision_and_signing_gives_version_2(client: Client) -> None:
    plan_id = proposed_id(client)
    post(client, f"/api/plans/{plan_id}/accept", SIGN)
    revision = post(client, f"/api/plans/{plan_id}/revise", {"monthly_amount": 50_000}).json()
    assert (revision["status"], revision["revises"], revision["monthly_amount"]) == ("proposed", plan_id, 50_000)
    assert client.get("/api/plans/active").json()["pending_revision"] == revision["id"]
    assert client.get(f"/api/plans/{revision['id']}/mandate").json()["version"] == 2
    assert post(client, f"/api/plans/{revision['id']}/accept", SIGN).json()["mandate_version"] == 2
    assert client.get("/api/plans/active").json()["id"] == revision["id"]
    assert client.get(f"/api/plans/{plan_id}").json()["status"] == "paused"


def test_revise_errors_name_the_field(client: Client) -> None:
    plan_id = proposed_id(client)
    post(client, f"/api/plans/{plan_id}/accept", SIGN)
    response = post(client, f"/api/plans/{plan_id}/revise", {"monthly_amount": 100_000})
    assert response.status_code == 422
    assert response.json()["field"] == "monthly_amount"


def test_ac8_other_customer_cannot_revise(client: Client) -> None:
    plan_id = proposed_id(client)
    post(client, f"/api/plans/{plan_id}/accept", SIGN)
    client.logout()
    client.force_login(create_customer("bob", AC1_SERIES))
    assert post(client, f"/api/plans/{plan_id}/revise", {"monthly_amount": 50_000}).status_code == 403
```

Run: `cd backend && uv run pytest tests/api/test_signing_api.py`
Expected: FAIL (`accept` ignores the password; `/revise` is 404/405).

- [ ] **Step 8: Schemas and routes**

In `backend/api/schemas.py`, append:

```python
class AcceptIn(Schema):
    password: str = Field(min_length=1, max_length=128)
```

and add `revises: int | None` and `pending_revision: int | None` to `PlanOut` (below `status`).

In `backend/api/routes.py`, add these two arguments to the `PlanOut(...)` call in `plan_out`:

```python
        revises=plan.revises_id,
        pending_revision=plan.revisions.filter(status=Plan.Status.PROPOSED)
        .values_list("pk", flat=True)
        .first(),
```

Then, add `AcceptIn` to the schema imports and `from django.core.exceptions import PermissionDenied`, and replace the accept route:

```python
@router.post("/plans/{plan_id}/accept", response=PlanOut)
def accept_plan(request: HttpRequest, plan_id: int, payload: AcceptIn) -> PlanOut:
    """Sign the mandate (AC7). The password confirms the signature (simulated strong customer
    authentication, ADR-0004). Ownership is checked first, so another customer's plan is 403
    whatever the password (AC8)."""
    plan = owned_plan(request, plan_id)
    if not current_user(request).check_password(payload.password):
        raise PermissionDenied("Incorrect password.")
    services.accept_plan(plan, get_clock())
    plan.refresh_from_db()
    return plan_out(plan)


@router.post("/plans/{plan_id}/revise", response=PlanOut)
def revise_plan(request: HttpRequest, plan_id: int, payload: AmountIn) -> PlanOut:
    """Propose a new amount for the active plan; nothing changes until it is signed (ADR-0004)."""
    return plan_out(
        services.revise_plan(owned_plan(request, plan_id), payload.monthly_amount, get_clock())
    )
```

- [ ] **Step 9: Update the tests that call accept (deliberate contract change)**

Accepting now needs the password, so every API test that accepts a plan must send it. This is the contract change of ADR-0004, not a loosened test: each test keeps its assertion.

Find them: `cd backend && grep -n '/accept"' tests/api`

- In `tests/api/test_plans_api.py`, add below `QUESTIONNAIRE`: `SIGN = {"password": "pw"}  # create_customer's password (ADR-0004)`, and change every `post(client, f"/api/plans/{...}/accept")` to `post(client, f"/api/plans/{...}/accept", SIGN)` (lines with `accept` in `test_main_flow_questionnaire_to_accepted_plan`, `test_ac6_low_confidence_transfer_is_approved_through_api`, `test_ac8_other_customer_cannot_view_or_accept_plan`, `test_accepting_a_rejected_plan_is_a_conflict`).
- In `tests/api/test_frontend_endpoints.py` and `tests/api/test_plan_details_api.py`, add the same `SIGN` constant and pass it to the accept calls.

Run: `cd backend && uv run pytest`
Expected: all pass. A failure in a test you did not edit means behaviour changed: stop and investigate (superpowers:systematic-debugging), do not edit that test.

- [ ] **Step 10: Docs and check**

In `docs/architecture.md`, data model section, add: `Plan.revises` (nullable, the accepted plan a proposal would replace; migration 0002, ADR-0004).

In `docs/traceability.md`, append to AC7: `; tests/api/test_signing_api.py::test_ac7_wrong_password_signs_nothing; tests/services/test_revision.py::test_ac7_signing_a_revision_twice_creates_orders_once`; to AC8: `; tests/api/test_signing_api.py::test_ac8_own_password_cannot_sign_another_customers_plan; tests/api/test_signing_api.py::test_ac8_other_customer_cannot_revise`.

In `README.md`, API paragraph: `accept` needs `{"password": ...}`; add `revise (new amount for the active plan, signed as the next mandate version)`.

Append to `docs/ai-usage.md` (AGENTS.md section 7: edited tests are explained in the AI usage log; the author verifies):

```markdown
### Case 4 — Signing needs the password: accept tests updated (DRAFT, author to verify)
- Phase: implementation
- Tool and model: Claude Code, Claude Opus 5.5 (frontend Figma plan, Task 4)
- Problem: Figma 07b confirms the mandate with the customer's password; the accept endpoint took no body.
- Context given and key instruction: the author chose "server checks the password" over a plain confirm dialog.
- Essence of the AI suggestion: `AcceptIn {password}`, ownership check first (AC8), then `check_password`;
  403 `Incorrect password.` creates nothing (ADR-0004).
- Decision: accepted. Consequence: the API tests that accept a plan (`tests/api/test_plans_api.py`,
  `test_frontend_endpoints.py`, `test_plan_details_api.py`) now send `{"password": "pw"}`. Their
  assertions are unchanged; the request contract changed, the tests were not loosened.
- Verification: `tests/api/test_signing_api.py`, full `make check`.
- Limitations of this verification: no rate limiting on wrong passwords (demo scope).
```

Add to `CHANGELOG.md`:

```markdown
### Changed
- Signing a mandate (`POST /api/plans/{id}/accept`) requires the customer's password; a wrong password signs nothing (AC7, ADR-0004).

### Added
- Plan revision: `POST /api/plans/{id}/revise` proposes a new amount for the active plan; signing it pauses the old plan and signs the next mandate version (ADR-0004, migration 0002).
```

Run: `make fmt && make check && cd backend && uv run python manage.py makemigrations --check --dry-run`
Expected: green; `No changes detected`.

- [ ] **Step 11: Suggested commit (user commits)**

```
feat(plans): password-confirmed signing and plan revision (AC7, ADR-0004)

API tests that accept a plan now send the password: deliberate contract change (ADR-0004).
```

---

### Task 5: Activity feed for the execution log (scheduled transfers, executions, plan events)

Deliverable: `GET /api/activity` returns the rows of the Figma execution log (frame `8:708`, component `3:210` "Execution log table row"): the next scheduled transfer of each active order, every execution with its audit fields, and the plan events, newest first, with customer-facing titles from templates. One new migration (`LogEntry.amount`).

**Files:**
- Modify: `backend/plans/models.py`; migration `backend/plans/migrations/0003_logentry_amount.py` via `makemigrations`
- Modify: `backend/plans/services.py`, `backend/plans/execution.py` (pass amounts to `log_event`)
- Modify: `backend/plans/explanations.py`
- Create: `backend/plans/activity.py`, `backend/tests/api/test_activity_api.py`
- Modify: `backend/tests/services/test_explanations.py`, `backend/api/schemas.py`, `backend/api/routes.py`
- Modify: `docs/architecture.md`, `docs/traceability.md` (AC6), `README.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `LogEntry`, `Execution`, `RecurringOrder`, `Mandate`, `services.active_plan(customer) -> Plan | None`, `services.log_event`, `plans.execution.idempotency_key(order, period) -> str`, `run_monthly_orders(clock)`, `next_transfer_on` (Task 3), `ItemKind`, `explanations.huf`, `SIGN` pattern (Task 4).
- Produces:
  - `log_event(..., amount: Huf | None = None)`; `LogEntry.amount: int | None`.
  - Templates: `explanations.transfer_title(kind: str, label: str, amount: Huf) -> str`, `explanations.event_title(event: str, *, amount: Huf | None, version: int | None, orders: int) -> str | None` (None: not shown), `explanations.scheduled_check(per_transfer_approval: bool) -> str`, `explanations.decision_text(clause: int, reason: str) -> str`.
  - `plans.activity.ActivityRow` (frozen dataclass) and `plans.activity.activity(customer: User, clock: Clock) -> list[ActivityRow]`.
  - API `GET /api/activity` → `ActivityOut[]`: `{key: str, on: date, title: str, amount: int | None, status: "scheduled" | "executed" | "denied" | "awaiting_approval" | "proposed" | "done" | "rejected" | "paused", mandate_version: int | None, clause: str | None, idempotency_key: str | None, logged_at: datetime | None, execution_id: int | None}`.

- [ ] **Step 1: Write the failing template tests**

Append to `backend/tests/services/test_explanations.py`:

```python
def test_activity_titles() -> None:
    assert explanations.transfer_title("emergency_fund", "Emergency fund", 30_000) == (
        "30,000 HUF to your emergency fund"
    )
    assert explanations.transfer_title("planned_expense", "New laptop", 30_000) == (
        "30,000 HUF to your New laptop savings"
    )
    assert explanations.transfer_title("investment", "Long-term investment", 13_500) == (
        "13,500 HUF to long-term investment"
    )
    assert explanations.event_title("plan_accepted", amount=73_500, version=1, orders=3) == (
        "You accepted the plan and signed mandate version 1: 3 monthly transfers set up"
    )
    assert explanations.event_title("plan_proposed", amount=73_500, version=None, orders=0) == (
        "Plan proposed: 73,500 HUF a month"
    )
    assert explanations.event_title("execution_executed", amount=1, version=1, orders=0) is None
    assert explanations.scheduled_check(False) == "Will be checked against §1 and §2"
    assert explanations.scheduled_check(True) == "Will be checked against §1, §2 and §3"
    assert explanations.decision_text(3, "This transfer needs your approval.") == (
        "§3 · This transfer needs your approval."
    )
```

Run: `cd backend && uv run pytest tests/services/test_explanations.py -k activity` — Expected: FAIL (`no attribute 'transfer_title'`).

- [ ] **Step 2: Implement the templates**

Append to `backend/plans/explanations.py`:

```python
TRANSFER_TITLES = {
    "emergency_fund": "{amount} HUF to your emergency fund",
    "planned_expense": "{amount} HUF to your {label} savings",
    "investment": "{amount} HUF to long-term investment",
}
EVENT_TITLES = {
    "plan_proposed": "Plan proposed: {amount} HUF a month",
    "plan_revised": "New amount proposed: {amount} HUF a month",
    "plan_edited": "Plan amount changed to {amount} HUF a month",
    "plan_accepted": (
        "You accepted the plan and signed mandate version {version}: {orders} monthly "
        "transfers set up"
    ),
    "plan_rejected": "You rejected the plan",
    "plan_paused": "Plan paused: mandate version {version} stopped (§4)",
}
SCHEDULED_CHECK = "Will be checked against {clauses}"
DECISION = "§{clause} · {reason}"


def transfer_title(kind: str, label: str, amount: Huf) -> str:
    return TRANSFER_TITLES[kind].format(amount=huf(amount), label=label)


def event_title(event: str, *, amount: Huf | None, version: int | None, orders: int) -> str | None:
    """Customer-facing title of a log event; None for events the activity feed does not show
    (executions appear as their own rows)."""
    template = EVENT_TITLES.get(event)
    if template is None:
        return None
    return template.format(amount=huf(amount or 0), version=version, orders=orders)


def scheduled_check(per_transfer_approval: bool) -> str:
    return SCHEDULED_CHECK.format(clauses="§1, §2 and §3" if per_transfer_approval else "§1 and §2")


def decision_text(clause: int, reason: str) -> str:
    return DECISION.format(clause=clause, reason=reason)
```

Run the Step 1 command again. Expected: PASS.

- [ ] **Step 3: `LogEntry.amount` and amounts in the log**

In `backend/plans/models.py`, add to `LogEntry` below `clause`:

```python
    amount = models.BigIntegerField(null=True, blank=True, help_text="Amount at the time, if any.")
```

Run: `cd backend && uv run python manage.py makemigrations plans --name logentry_amount`
Expected: `0003_logentry_amount.py` with one `AddField`.

In `backend/plans/services.py`, add a keyword parameter `amount: Huf | None = None` to `log_event` and pass `amount=amount` to `LogEntry.objects.create`. Then pass amounts at these calls:
- `plan_proposed` in `propose_plan`: `amount=proposal.monthly_amount`
- `plan_accepted` in `accept_plan`: `amount=plan.monthly_amount`
- `plan_edited` in `edit_amount`: `amount=monthly_amount`
- `plan_revised` in `revise_plan`: `amount=monthly_amount`

In `backend/plans/execution.py`, pass `amount=order.monthly_amount` to the `log_event` call in `execute_order`.

Run: `cd backend && uv run pytest` — Expected: all pass (no behaviour change).

- [ ] **Step 4: Write the failing API tests**

`backend/tests/api/test_activity_api.py`:

```python
from typing import Any

import pytest
from django.test import Client

from banking.models import Product
from core.clock import FixedClock
from plans.execution import run_monthly_orders
from plans.models import RecurringOrder
from tests.constants import AC1_SERIES
from tests.factories import create_catalogue, create_customer

pytestmark = pytest.mark.django_db

ANSWERS: dict[str, Any] = {"risk_score": 3, "existing_emergency_fund": 0, "planned_expenses": []}
SIGN = {"password": "pw"}


@pytest.fixture(autouse=True)
def catalogue() -> list[Product]:
    return create_catalogue()


def post(client: Client, url: str, body: dict[str, Any] | None = None) -> Any:
    return client.post(url, body or {}, content_type="application/json")


def accepted(client: Client, username: str, surpluses: list[int]) -> dict[str, Any]:
    client.force_login(create_customer(username, surpluses))
    post(client, "/api/questionnaire", ANSWERS)
    plan: dict[str, Any] = post(client, "/api/plans").json()["plan"]
    assert post(client, f"/api/plans/{plan['id']}/accept", SIGN).status_code == 200
    return plan


def test_activity_shows_scheduled_transfers_then_events(client: Client) -> None:
    plan = accepted(client, "anna", AC1_SERIES)
    rows = client.get("/api/activity").json()
    scheduled = [r for r in rows if r["status"] == "scheduled"]
    orders = RecurringOrder.objects.filter(plan_item__plan_id=plan["id"]).order_by("id")
    assert [r["idempotency_key"] for r in scheduled] == [f"order-{o.pk}-2026-11" for o in orders]
    assert {r["on"] for r in scheduled} == {"2026-11-01"}
    assert {r["clause"] for r in scheduled} == {"Will be checked against §1 and §2"}
    assert {r["logged_at"] for r in scheduled} == {None}
    events = rows[len(scheduled):]
    assert [(r["title"], r["status"]) for r in events] == [
        (
            f"You accepted the plan and signed mandate version 1: {len(plan['items'])} monthly "
            "transfers set up",
            "done",
        ),
        ("Plan proposed: 73,500 HUF a month", "proposed"),
    ]
    assert events[0]["amount"] == 73_500 and events[0]["mandate_version"] == 1


def test_ac6_waiting_transfer_offers_approval(client: Client, clock: FixedClock) -> None:
    accepted(client, "dani", [50_000, 60_000, 55_000, 65_000])
    run_monthly_orders(clock)
    [waiting] = [r for r in client.get("/api/activity").json() if r["status"] == "awaiting_approval"]
    assert waiting["execution_id"] is not None
    assert waiting["clause"] == "§3 · This transfer needs your approval."
    assert waiting["on"] == "2026-10-01" and waiting["logged_at"] is not None
    assert post(client, f"/api/executions/{waiting['execution_id']}/approve").status_code == 200
    statuses = {r["key"]: r["status"] for r in client.get("/api/activity").json()}
    assert statuses[waiting["key"]] == "executed"


def test_activity_is_private(client: Client) -> None:
    accepted(client, "anna", AC1_SERIES)
    client.logout()
    client.force_login(create_customer("bob", AC1_SERIES))
    assert client.get("/api/activity").json() == []
```

Run: `cd backend && uv run pytest tests/api/test_activity_api.py`
Expected: FAIL — `/api/activity` is 404.

- [ ] **Step 5: Implement the activity rows**

`backend/plans/activity.py`:

```python
"""Rows of the customer's execution log (Figma 08): the next scheduled transfer of each active
order, every execution with its audit fields, and plan events. Titles come from templates."""

from dataclasses import dataclass
from datetime import date, datetime

from django.contrib.auth.models import User

from core.clock import Clock
from plans import explanations
from plans.execution import idempotency_key
from plans.models import Execution, LogEntry, Plan, RecurringOrder
from plans.services import active_plan
from rules.money import Huf
from rules.months import next_transfer_on

EVENT_STATUS = {
    "plan_proposed": "proposed",
    "plan_revised": "proposed",
    "plan_edited": "done",
    "plan_accepted": "done",
    "plan_rejected": "rejected",
    "plan_paused": "paused",
}


@dataclass(frozen=True)
class ActivityRow:
    key: str
    on: date
    title: str
    amount: Huf | None
    status: str
    mandate_version: int | None
    clause: str | None
    idempotency_key: str | None
    logged_at: datetime | None
    execution_id: int | None


def _scheduled(plan: Plan | None, period: date) -> list[ActivityRow]:
    if plan is None or plan.status != Plan.Status.ACCEPTED:
        return []
    orders = (
        RecurringOrder.objects.filter(plan_item__plan=plan, status=RecurringOrder.Status.ACTIVE)
        .select_related("plan_item", "mandate")
        .order_by("id")
    )
    return [
        ActivityRow(
            key=f"scheduled-{order.pk}-{period:%Y-%m}",
            on=period,
            title=explanations.transfer_title(
                order.plan_item.kind, order.plan_item.label, order.monthly_amount
            ),
            amount=order.monthly_amount,
            status="scheduled",
            mandate_version=order.mandate.version,
            clause=explanations.scheduled_check(order.mandate.per_transfer_approval),
            idempotency_key=idempotency_key(order, period),
            logged_at=None,
            execution_id=None,
        )
        for order in orders
        if not Execution.objects.filter(idempotency_key=idempotency_key(order, period)).exists()
    ]


def _executions(customer: User) -> list[ActivityRow]:
    rows = Execution.objects.filter(order__mandate__customer=customer).select_related(
        "order__plan_item"
    )
    return [
        ActivityRow(
            key=f"execution-{e.pk}",
            on=e.period,
            title=explanations.transfer_title(
                e.order.plan_item.kind, e.order.plan_item.label, e.amount
            ),
            amount=e.amount,
            status=e.status,
            mandate_version=e.mandate_version,
            clause=explanations.decision_text(e.clause, e.reason),
            idempotency_key=e.idempotency_key,
            logged_at=e.created_at,
            execution_id=e.pk,
        )
        for e in rows
    ]


def _events(customer: User) -> list[ActivityRow]:
    rows = []
    for entry in LogEntry.objects.filter(customer=customer, event__in=EVENT_STATUS).select_related(
        "plan"
    ):
        orders = entry.plan.items.count() if entry.plan is not None else 0
        title = explanations.event_title(
            entry.event, amount=entry.amount, version=entry.mandate_version, orders=orders
        )
        if title is None:
            continue
        rows.append(
            ActivityRow(
                key=f"event-{entry.pk}",
                on=entry.created_at.date(),
                title=title,
                amount=entry.amount,
                status=EVENT_STATUS[entry.event],
                mandate_version=entry.mandate_version,
                clause=None,
                idempotency_key=None,
                logged_at=entry.created_at,
                execution_id=None,
            )
        )
    return rows


def _newest_first(row: ActivityRow) -> tuple[date, datetime, int]:
    """Sort key: date, log time, then database id (FixedClock gives equal log times in tests)."""
    assert row.logged_at is not None  # executions and events are always logged
    return (row.on, row.logged_at, int(row.key.rsplit("-", 1)[1]))


def activity(customer: User, clock: Clock) -> list[ActivityRow]:
    """Newest first: scheduled transfers, then executions and events."""
    scheduled = _scheduled(active_plan(customer), next_transfer_on(clock.today()))
    logged = sorted(_executions(customer) + _events(customer), key=_newest_first, reverse=True)
    return scheduled + logged
```

- [ ] **Step 6: Schema and route**

Append to `backend/api/schemas.py`:

```python
class ActivityOut(Schema):
    key: str
    on: date
    title: str
    amount: int | None
    status: str
    mandate_version: int | None
    clause: str | None
    idempotency_key: str | None
    logged_at: datetime | None
    execution_id: int | None
```

Append to `backend/api/routes.py` (import `ActivityOut` and `from plans import activity as activities`):

```python
@router.get("/activity", response=list[ActivityOut])
def list_activity(request: HttpRequest) -> list[ActivityOut]:
    """The customer's execution log (Figma 08 and Activity): only their own rows (AC8)."""
    rows = activities.activity(current_user(request), get_clock())
    return [ActivityOut(**vars(row)) for row in rows]
```

Run: `cd backend && uv run pytest`
Expected: all pass. The two log entries in `test_activity_shows_scheduled_transfers_then_events` share `created_at` (FixedClock); `_newest_first` breaks the tie by database id, so the later event (accepted) comes first.

- [ ] **Step 7: Docs and check**

`docs/architecture.md`, data model: add `LogEntry.amount` (nullable, migration 0003); add a line under "Main flow": `GET /api/activity` merges scheduled transfers (next period of each active order), executions and plan events (`plans/activity.py`).

`docs/traceability.md`, AC6 evidence: append `; tests/api/test_activity_api.py::test_ac6_waiting_transfer_offers_approval`.

`README.md`, API paragraph: add `activity (execution log: scheduled transfers, executions, plan events)`.

`CHANGELOG.md`, `### Added`: `- API: GET /api/activity, the execution log with scheduled transfers, audit fields (mandate version, clause, idempotency key) and plan events; log entries store the amount (migration 0003) (AC6, AC7).`

Run: `make fmt && make check && cd backend && uv run python manage.py makemigrations --check --dry-run`
Expected: green; `No changes detected`.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(api): activity feed for the execution log (AC6)`

---

### Task 6: API types, fetch client with CSRF, query client, test helpers

Deliverable: a typed `apiFetch` that sends the current CSRF token, turns error bodies into readable messages, and test helpers that stub the API.

**Files:**
- Create: `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/api/client.test.ts`, `frontend/src/api/queryClient.ts`
- Create: `frontend/src/test/render.tsx`, `frontend/src/test/fixtures.ts`
- Modify: `frontend/src/test/setup.ts`, `CHANGELOG.md`

**Interfaces:**
- Consumes: the API contract after backend Tasks 2–5 of this plan (`backend/api/schemas.py`).
- Produces:
  - `types.ts`: `Huf`, `Role`, `Me`, `LoginIn`, `ExpenseIn`, `QuestionnaireIn`, `IdOut`, `Confidence`, `PlanStatus`, `Outcome`, `ItemKind`, `ProductOut`, `PlanItemOut`, `PlanOut`, `ProposalOut`, `MonthOut`, `AnalysisOut`, `BacktestMonthOut`, `TimeMachineOut`, `ExecutionStatus`, `ExecutionOut`, `ActivityStatus`, `ActivityOut`, `TransactionOut`, `AccountOut`, `RulesOut`, `ClauseOut`, `MandateStatus`, `MandateOut`
  - `client.ts`: `class ApiError extends Error { status: number; field: string | null }`, `apiFetch<T>(path: string, options?: { method?: "GET" | "POST" | "PATCH"; body?: unknown }): Promise<T>`
  - `queryClient.ts`: `makeQueryClient(onUnauthorized?: () => void): QueryClient`
  - `render.tsx`: `mockApi(routes: Record<string, Handler>): Call[]`, `renderScreen(element, { path?, url? }): QueryClient`, types `Reply`, `Handler`, `Call`
  - `fixtures.ts`: `PLAN`, `plan(overrides?)`, `LOW_CONFIDENCE_PLAN`, `ANALYSIS`, `MACHINE`

- [ ] **Step 1: Write the API types (mirror of `backend/api/schemas.py`)**

`frontend/src/api/types.ts`:

```ts
/**
 * Mirror of backend/api/schemas.py (after backend Tasks 2–5). Keep field names and enum values
 * identical. Dates are ISO strings ("2026-09-01"); datetimes are ISO strings with time.
 */

/** Whole forints. Always an integer; the frontend never does arithmetic on money. */
export type Huf = number;

export type Role = "customer" | "admin";

export interface Me {
  username: string;
  role: Role;
}

export interface LoginIn {
  username: string;
  password: string;
}

export interface ExpenseIn {
  name: string;
  amount: Huf;
  due_on: string;
}

export interface QuestionnaireIn {
  risk_score: number;
  existing_emergency_fund: Huf;
  expected_monthly_savings: Huf | null;
  planned_expenses: ExpenseIn[];
}

export interface IdOut {
  id: number;
}

export type Confidence = "none" | "low" | "normal";
export type PlanStatus = "proposed" | "accepted" | "rejected" | "paused";
export type Outcome = "plan" | "no_surplus" | "needs_expected_savings";
export type ItemKind = "emergency_fund" | "planned_expense" | "investment";

export interface ProductOut {
  id: number;
  name: string;
  risk_level: number;
  liquid: boolean;
}

export interface PlanItemOut {
  position: number;
  kind: ItemKind;
  label: string;
  product: ProductOut;
  monthly_amount: Huf;
  target_amount: Huf | null;
  due_on: string | null;
  saved_amount: Huf;
  progress_percent: number | null;
}

export interface PlanOut {
  id: number;
  status: PlanStatus;
  revises: number | null;
  pending_revision: number | null;
  created_on: string;
  monthly_amount: Huf;
  proposed_amount: Huf;
  median_surplus: Huf | null;
  months_of_data: number;
  share_percent: number;
  risk_score: number;
  min_balance: Huf;
  confidence: Confidence;
  per_transfer_approval: boolean;
  next_transfer_on: string;
  mandate_version: number | null;
  signed_on: string | null;
  saved_total: Huf;
  items: PlanItemOut[];
  explanations: string[];
}

export interface ProposalOut {
  outcome: Outcome;
  plan: PlanOut | null;
  explanations: string[];
}

export interface MonthOut {
  month: string;
  income: Huf;
  expenses: Huf;
  surplus: Huf;
}

export interface AnalysisOut {
  months_of_data: number;
  confidence: Confidence;
  median_surplus: Huf | null;
  median_expenses: Huf;
  monthly_amount: Huf | null;
  share_percent: number;
  median_explanation: string | null;
  explanations: string[];
  months: MonthOut[];
}

export interface BacktestMonthOut {
  month: string;
  balance_before_transfer: Huf;
  transfer: Huf;
  skipped: boolean;
  balance_after: Huf;
  saved_to_date: Huf;
  note: string | null;
}

export interface TimeMachineOut {
  total_saved: Huf;
  months_replayed: number;
  transfers_made: number;
  skipped_months: string[];
  months: BacktestMonthOut[];
}

export type ExecutionStatus = "executed" | "denied" | "awaiting_approval";

export interface ExecutionOut {
  id: number;
  period: string;
  status: ExecutionStatus;
  amount: Huf;
  mandate_version: number;
  clause: number;
  reason: string;
}

export type ActivityStatus =
  | "scheduled"
  | ExecutionStatus
  | "proposed"
  | "done"
  | "rejected"
  | "paused";

export interface ActivityOut {
  key: string;
  on: string;
  title: string;
  amount: Huf | null;
  status: ActivityStatus;
  mandate_version: number | null;
  clause: string | null;
  idempotency_key: string | null;
  logged_at: string | null;
  execution_id: number | null;
}

export interface TransactionOut {
  id: number;
  booked_on: string;
  amount: Huf;
  description: string;
  own_transfer: boolean;
}

export interface AccountOut {
  today: string;
  name: string;
  balance: Huf;
  min_balance: Huf;
  transactions: TransactionOut[];
}

export interface RulesOut {
  lines: string[];
}

export interface ClauseOut {
  number: number;
  text: string;
}

export type MandateStatus = "unsigned" | "active" | "paused";

export interface MandateOut {
  status: MandateStatus;
  version: number;
  signed_at: string | null;
  max_monthly_amount: Huf;
  min_balance: Huf;
  per_transfer_approval: boolean;
  products: ProductOut[];
  clauses: ClauseOut[];
}
```

- [ ] **Step 2: Write the failing client tests**

`frontend/src/api/client.test.ts`:

```ts
import { beforeEach, expect, test } from "vitest";
import { mockApi } from "../test/render";
import { ApiError, apiFetch } from "./client";

function clearCsrfCookie(): void {
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
}

beforeEach(clearCsrfCookie);

test("GET parses JSON and sends no CSRF header", async () => {
  const calls = mockApi({ "GET /api/auth/me": { body: { username: "anna", role: "customer" } } });
  await expect(apiFetch("/api/auth/me")).resolves.toEqual({ username: "anna", role: "customer" });
  expect(calls[0]?.headers["X-CSRFToken"]).toBeUndefined();
});

test("uses the current csrftoken cookie on every unsafe request", async () => {
  const calls = mockApi({ "POST /api/plans": { body: {} } });
  document.cookie = "csrftoken=before-login";
  await apiFetch("/api/plans", { method: "POST" });
  document.cookie = "csrftoken=after-login"; // Django rotates the token on login
  await apiFetch("/api/plans", { method: "POST" });
  expect(calls.map((call) => call.headers["X-CSRFToken"])).toEqual(["before-login", "after-login"]);
});

test("fetches a CSRF token first when there is no cookie", async () => {
  const calls = mockApi({
    "GET /api/auth/csrf": { body: { csrftoken: "fresh" } },
    "POST /api/auth/logout": { body: { ok: true } },
  });
  await apiFetch("/api/auth/logout", { method: "POST" });
  expect(calls.map((call) => `${call.method} ${call.path}`)).toEqual([
    "GET /api/auth/csrf",
    "POST /api/auth/logout",
  ]);
  expect(calls[1]?.headers["X-CSRFToken"]).toBe("fresh");
});

test("sends a JSON body", async () => {
  document.cookie = "csrftoken=t";
  const calls = mockApi({ "PATCH /api/plans/7": { body: {} } });
  await apiFetch("/api/plans/7", { method: "PATCH", body: { monthly_amount: 50_000 } });
  expect(calls[0]?.body).toEqual({ monthly_amount: 50_000 });
  expect(calls[0]?.headers["Content-Type"]).toBe("application/json");
});

test("a string detail becomes the error message", async () => {
  mockApi({ "GET /api/plans/9": { status: 403, body: { detail: "This plan belongs to another customer." } } });
  await expect(apiFetch("/api/plans/9")).rejects.toEqual(
    new ApiError(403, "This plan belongs to another customer."),
  );
});

test("a validation error list becomes one readable message", async () => {
  mockApi({
    "GET /api/x": {
      status: 422,
      body: { detail: [{ type: "greater_than", loc: ["body"], msg: "Input should be greater than 0" }] },
    },
  });
  const error = await apiFetch("/api/x").catch((caught: unknown) => caught);
  expect(error).toBeInstanceOf(ApiError);
  expect(error).toMatchObject({ status: 422, message: "Input should be greater than 0" });
});

test("a 422 keeps the field the backend names", async () => {
  mockApi({
    "POST /api/questionnaire": {
      status: 422,
      body: { detail: "The due date of 'Holiday' (2026-09-01) is in the past.", field: "planned_expenses.1.due_on" },
    },
  });
  await expect(apiFetch("/api/questionnaire", { method: "POST", body: {} })).rejects.toMatchObject({
    status: 422,
    field: "planned_expenses.1.due_on",
  });
});

test("a non-JSON error page still gives a message", async () => {
  mockApi({ "GET /api/x": { status: 500, raw: "<h1>Server Error</h1>" } });
  await expect(apiFetch("/api/x")).rejects.toThrow("Request failed (500).");
});

test("an empty success body resolves to null", async () => {
  mockApi({ "GET /api/x": { status: 200 } });
  await expect(apiFetch("/api/x")).resolves.toBeNull();
});
```

- [ ] **Step 3: Write the test helpers**

`frontend/src/test/render.tsx`:

```tsx
import { QueryClientProvider, type QueryClient } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { vi } from "vitest";
import { makeQueryClient } from "../api/queryClient";

/** `body` is sent as JSON; `raw` is sent as-is (for non-JSON error pages). */
export interface Reply {
  status?: number;
  body?: unknown;
  raw?: string;
}
export type Handler = Reply | ((body: unknown) => Reply | Promise<Reply>);
export interface Call {
  method: string;
  path: string;
  body: unknown;
  headers: Record<string, string>;
}

/**
 * Stub fetch. Keys are "METHOD /path", e.g. "POST /api/plans/7/accept".
 * Unmocked requests answer 500 with the request in the message, so a missing mock is visible.
 * Returns the list of calls, in order.
 */
export function mockApi(routes: Record<string, Handler>): Call[] {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string, init: RequestInit = {}) => {
      const method = init.method ?? "GET";
      const body: unknown = typeof init.body === "string" ? JSON.parse(init.body) : undefined;
      calls.push({ method, path, body, headers: (init.headers ?? {}) as Record<string, string> });
      const handler = routes[`${method} ${path}`];
      const reply: Reply =
        handler === undefined
          ? { status: 500, body: { detail: `Unmocked request: ${method} ${path}` } }
          : typeof handler === "function"
            ? await handler(body)
            : handler;
      const text = reply.raw ?? (reply.body === undefined ? null : JSON.stringify(reply.body));
      return new Response(text, { status: reply.status ?? 200 });
    }),
  );
  return calls;
}

function LocationProbe() {
  const location = useLocation();
  return <p>Navigated to {location.pathname}</p>;
}

/**
 * Render one screen at `url`, matched by the route `path` (e.g. "/plans/:planId").
 * Navigating anywhere else renders "Navigated to <pathname>".
 */
export function renderScreen(
  element: ReactElement,
  { path = "/", url = path }: { path?: string; url?: string } = {},
): QueryClient {
  const queryClient = makeQueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path={path} element={element} />
          <Route path="*" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return queryClient;
}
```

`frontend/src/test/fixtures.ts`:

```ts
import type { AnalysisOut, PlanOut, TimeMachineOut } from "../api/types";

/** The Figma 05 plan for anna: 73,500 HUF from a 105,000 HUF median (AC1), split 30k/30k/13.5k. */
export const PLAN: PlanOut = {
  id: 7,
  status: "proposed",
  revises: null,
  pending_revision: null,
  created_on: "2026-10-08",
  monthly_amount: 73_500,
  proposed_amount: 73_500,
  median_surplus: 105_000,
  months_of_data: 6,
  share_percent: 70,
  risk_score: 2,
  min_balance: 100_000,
  confidence: "normal",
  per_transfer_approval: false,
  next_transfer_on: "2026-11-01",
  mandate_version: null,
  signed_on: null,
  saved_total: 0,
  items: [
    {
      position: 0,
      kind: "emergency_fund",
      label: "Emergency fund",
      product: { id: 1, name: "Short government bond fund", risk_level: 2, liquid: true },
      monthly_amount: 30_000,
      target_amount: 750_000,
      due_on: null,
      saved_amount: 720_000,
      progress_percent: 96,
    },
    {
      position: 1,
      kind: "planned_expense",
      label: "New laptop",
      product: { id: 1, name: "Short government bond fund", risk_level: 2, liquid: true },
      monthly_amount: 30_000,
      target_amount: 300_000,
      due_on: "2027-08-01",
      saved_amount: 0,
      progress_percent: 0,
    },
    {
      position: 2,
      kind: "investment",
      label: "Long-term investment",
      product: { id: 1, name: "Short government bond fund", risk_level: 2, liquid: true },
      monthly_amount: 13_500,
      target_amount: null,
      due_on: null,
      saved_amount: 0,
      progress_percent: null,
    },
  ],
  explanations: [
    "We suggest saving 73,500 HUF a month: 70% of your median monthly surplus of 105,000 HUF.",
  ],
};

export function plan(overrides: Partial<PlanOut> = {}): PlanOut {
  return { ...PLAN, ...overrides };
}

/** Figma 05b: dani, 4 months of data, low confidence (AC6). */
export const LOW_CONFIDENCE_PLAN: PlanOut = plan({
  id: 8,
  monthly_amount: 40_250,
  proposed_amount: 40_250,
  median_surplus: 57_500,
  months_of_data: 4,
  confidence: "low",
  per_transfer_approval: true,
  explanations: [
    "We suggest saving 40,250 HUF a month: 70% of your median monthly surplus of 57,500 HUF.",
    "This plan is based on only 4 months of data, so its confidence is low. Every transfer will ask for your approval.",
  ],
});

export const ANALYSIS: AnalysisOut = {
  months_of_data: 6,
  confidence: "normal",
  median_surplus: 105_000,
  median_expenses: 250_000,
  monthly_amount: 73_500,
  share_percent: 70,
  median_explanation:
    "Sorted: 80,000 · 90,000 · 100,000 · 110,000 · 120,000 · 300,000. Median = (100,000 + 110,000) / 2 = 105,000 HUF.",
  explanations: [],
  months: [
    ["2026-04-01", 100_000],
    ["2026-05-01", 120_000],
    ["2026-06-01", 80_000],
    ["2026-07-01", 110_000],
    ["2026-08-01", 90_000],
    ["2026-09-01", 300_000],
  ].map(([month, surplus]) => ({
    month: String(month),
    income: 400_000,
    expenses: 400_000 - Number(surplus),
    surplus: Number(surplus),
  })),
};

const SKIP_NOTE = (month: string) =>
  `${month}: the transfer was skipped because it would have left less than 100,000 HUF on your account.`;

/** An illustrative 3-month replay with one skipped month (AC4). */
export const MACHINE: TimeMachineOut = {
  total_saved: 147_000,
  months_replayed: 3,
  transfers_made: 2,
  skipped_months: ["2025-12-01"],
  months: [
    { month: "2025-10-01", balance_before_transfer: 400_000, transfer: 73_500, skipped: false, balance_after: 326_500, saved_to_date: 73_500, note: null },
    { month: "2025-11-01", balance_before_transfer: 350_000, transfer: 73_500, skipped: false, balance_after: 276_500, saved_to_date: 147_000, note: null },
    { month: "2025-12-01", balance_before_transfer: 150_000, transfer: 0, skipped: true, balance_after: 150_000, saved_to_date: 147_000, note: SKIP_NOTE("2025-12") },
  ],
};
```

The fixture builders use arithmetic on test data only (`400_000 - surplus`); `src/**/*.test.*` and `src/test/` are test code, not app code.

Add to `frontend/src/test/setup.ts` (below the existing `afterEach`), so screen tests never need a CSRF mock:

```ts
beforeEach(() => {
  document.cookie = "csrftoken=test-token";
});
```

and change its vitest import to `import { afterEach, beforeEach, vi } from "vitest";`.

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/api`
Expected: FAIL with `Failed to resolve import "./client"` (or `../api/queryClient`).

- [ ] **Step 5: Implement the client and the query client**

`frontend/src/api/client.ts`:

```ts
/**
 * The only place that calls fetch. Same-origin requests (Vite proxies /api), session cookie auth.
 * Unsafe methods send X-CSRFToken read from the cookie on every request: Django rotates the token
 * on login, so a cached token would be rejected with 403.
 */

export class ApiError extends Error {
  readonly status: number;
  /** The input the backend blames, e.g. "planned_expenses.1.due_on" (backend Task 3). */
  readonly field: string | null;

  constructor(status: number, message: string, field: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.field = field;
  }
}

interface Options {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
}

/** Ninja sends {"detail": "text"} for our errors and {"detail": [{msg, ...}]} for schema errors. */
function messageFrom(body: unknown, status: number): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const { detail } = body;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item: unknown) =>
          typeof item === "object" && item !== null && "msg" in item && typeof item.msg === "string"
            ? item.msg
            : "",
        )
        .filter((text) => text !== "");
      if (messages.length > 0) return messages.join(" ");
    }
  }
  return `Request failed (${status}).`;
}

function fieldFrom(body: unknown): string | null {
  if (typeof body === "object" && body !== null && "field" in body && typeof body.field === "string") {
    return body.field;
  }
  return null;
}

function parseJson(text: string): unknown {
  if (text === "") return null;
  try {
    return JSON.parse(text);
  } catch {
    return null; // e.g. Django's HTML error page
  }
}

function readCookie(name: string): string | null {
  const prefix = `${name}=`;
  const match = document.cookie.split("; ").find((part) => part.startsWith(prefix));
  if (match === undefined || match.length === prefix.length) return null;
  return decodeURIComponent(match.slice(prefix.length));
}

async function csrfToken(): Promise<string> {
  const current = readCookie("csrftoken");
  if (current !== null) return current;
  const { csrftoken } = await apiFetch<{ csrftoken: string }>("/api/auth/csrf");
  return csrftoken;
}

export async function apiFetch<T>(path: string, options: Options = {}): Promise<T> {
  const method = options.method ?? "GET";
  const headers: Record<string, string> = {};
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") headers["X-CSRFToken"] = await csrfToken();
  const response = await fetch(path, {
    method,
    headers,
    credentials: "same-origin",
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const data = parseJson(await response.text());
  if (!response.ok) {
    throw new ApiError(response.status, messageFrom(data, response.status), fieldFrom(data));
  }
  return data as T;
}
```

`frontend/src/api/queryClient.ts`:

```ts
import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";
import { ApiError } from "./client";

/**
 * No retries: 4xx answers are final, and retrying a 404 or 401 only delays the UI.
 * `onUnauthorized` runs when any request answers 401 (session expired).
 */
export function makeQueryClient(onUnauthorized: () => void = () => undefined): QueryClient {
  const onError = (error: Error) => {
    if (error instanceof ApiError && error.status === 401) onUnauthorized();
  };
  return new QueryClient({
    queryCache: new QueryCache({ onError }),
    mutationCache: new MutationCache({ onError }),
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass (9 client tests + 1 app test).

- [ ] **Step 7: Lint, changelog**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend API client: typed mirror of the API schemas, CSRF token read on every request, readable messages for 403 / 409 / 422 errors and the field a 422 names.
```

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): typed api client with csrf handling and test helpers`

---

### Task 7: Figma tokens, formatting and base components

Deliverable: `theme.css` holds the Figma variables verbatim; money / date formatting and parsing; the base components of the Figma `Components` board (frame `2:3`): `Icon`, `Button`, `Badge`, `TextField`, `Checkbox`, `ErrorMessage`, `Card`, `StatTile`, `Kbd`, `ProgressBar`. A token guard test forbids hex colours, arbitrary values and client clock reads.

**Files:**
- Modify: `frontend/src/main.tsx` (font import), `frontend/src/theme/theme.css`
- Create: `frontend/src/theme/tokens.test.ts`, `frontend/src/format.ts`, `frontend/src/format.test.ts`
- Create: `frontend/src/components/{Icon,Button,Badge,TextField,Checkbox,ErrorMessage,Card,StatTile,Kbd,ProgressBar}.tsx`, `frontend/src/components/components.test.tsx`
- Modify: `CHANGELOG.md`, `docs/tasks.md`

**Interfaces:**
- Consumes: `Huf`, `ActivityStatus`, `Confidence` (Task 6).
- Produces:
  - Tailwind utilities from tokens: colours `bg surface surface-hover text text-muted border border-strong primary primary-hover primary-subtle on-primary danger danger-bg success success-bg warning warning-bg info info-bg focus-ring tooltip-bg chart-saved chart-income chart-skipped chart-grid`; spacing `touch` (44px), `sidebar` (248px), `panel` (360px), `content` (1040px), `narrow` (720px); radius `sm md lg full`; shadows `panel`, `focus`; text sizes `h1 h2 h3 body caption number`; font `sans` (Inter).
  - `format.ts`: `formatHuf(amount): string` (`73500` → `"73,500 HUF"`), `formatNumber(amount): string` (`"1,220,000"`), `formatSigned(amount): string` (`"+550,000 HUF"` / `"−150,000 HUF"`), `formatMonth(iso)` (`"2026-09"`), `formatDay(iso)` (`"2026-10-06"`), `monthName(iso)` (`"Oct"`), `monthYear(iso)` (`"2025"`), `displayName(username)` (`"anna"` → `"Anna"`), `parseHuf(text): Huf | null`, `AMOUNT_HINT`.
  - `Icon({ name: IconName, className? })`, `type IconName = "home" | "savings" | "activity" | "profile" | "alert" | "arrow-left" | "check" | "chevron-down" | "chevron-right" | "close" | "history" | "info" | "lock" | "log-out" | "menu" | "enter"`.
  - `Button({ variant?: "primary" | "secondary" | "ghost" | "danger", ...buttonProps })`, `buttonClass(variant?): string`.
  - `Badge({ tone: BadgeTone, children })`, `type BadgeTone = "success" | "warning" | "info" | "neutral"`, `statusBadge(status: ActivityStatus): { tone: BadgeTone; label: string }`, `confidenceBadge(confidence: Confidence): { tone: BadgeTone; label: string }`.
  - `TextField({ label, hint?, error?, suffix?, ...inputProps })` — `aria-invalid` and `aria-describedby` when `error`.
  - `Checkbox({ label, ...inputProps })`, `ErrorMessage({ error: unknown })`, `Card({ title?, children, className? })`, `StatTile({ label, value, caption? })`, `Kbd({ children })`, `ProgressBar({ label, percent: number })`.

- [ ] **Step 1: Write the failing tests**

`frontend/src/format.test.ts`:

```ts
import { describe, expect, test } from "vitest";
import {
  displayName,
  formatDay,
  formatHuf,
  formatMonth,
  formatNumber,
  formatSigned,
  monthName,
  monthYear,
  parseHuf,
} from "./format";

test("formatHuf matches the backend explanation format", () => {
  expect(formatHuf(73_500)).toBe("73,500 HUF");
  expect(formatHuf(-40_000)).toBe("-40,000 HUF");
  expect(formatHuf(0)).toBe("0 HUF");
  expect(formatNumber(1_220_000)).toBe("1,220,000");
});

test("formatSigned marks income and expenses like Figma 02", () => {
  expect(formatSigned(550_000)).toBe("+550,000 HUF");
  expect(formatSigned(-150_000)).toBe("−150,000 HUF");
});

test("dates are sliced, never shifted by time zone", () => {
  expect(formatMonth("2026-09-01")).toBe("2026-09");
  expect(formatDay("2026-10-06T23:30:00Z")).toBe("2026-10-06");
  expect(monthName("2025-12-01")).toBe("Dec");
  expect(monthYear("2025-12-01")).toBe("2025");
});

test("displayName capitalises the username", () => {
  expect(displayName("anna")).toBe("Anna");
});

describe("parseHuf", () => {
  test.each([
    ["250000", 250_000],
    ["250 000", 250_000],
    ["250,000", 250_000],
    [" 0 ", 0],
  ])("accepts %j", (text, expected) => {
    expect(parseHuf(text)).toBe(expected);
  });

  test.each(["", "   ", "-5", "-50,000", "100.5", "100.0", "1e5", "abc", "12a", "99999999999999999999"])(
    "rejects %j",
    (text) => {
      expect(parseHuf(text)).toBeNull();
    },
  );
});
```

`frontend/src/theme/tokens.test.ts`:

```ts
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "vitest";

const SRC = fileURLToPath(new URL("..", import.meta.url));
// Hex colours or Tailwind arbitrary values ("p-[13px]") bypass the Figma tokens.
const RAW_STYLE = /#[0-9a-fA-F]{3,8}\b|\b[\w:-]+-\[[^\]]+\]/;
// "Today" comes from the API (SAVERAI_FIXED_DATE); the client clock must not decide anything.
const CLIENT_CLOCK = /new Date\(|Date\.now\(/;

function appFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return entry.name === "test" ? [] : appFiles(path);
    return /\.tsx?$/.test(entry.name) && !entry.name.includes(".test.") ? [path] : [];
  });
}

test("app code uses only theme tokens", () => {
  const offenders = appFiles(SRC).filter((file) => RAW_STYLE.test(readFileSync(file, "utf8")));
  expect(offenders).toEqual([]);
});

test("app code never reads the client clock", () => {
  const offenders = appFiles(SRC).filter((file) => CLIENT_CLOCK.test(readFileSync(file, "utf8")));
  expect(offenders).toEqual([]);
});
```

`frontend/src/components/components.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Badge, confidenceBadge, statusBadge } from "./Badge";
import { Button } from "./Button";
import { Checkbox } from "./Checkbox";
import { ErrorMessage } from "./ErrorMessage";
import { Icon } from "./Icon";
import { ProgressBar } from "./ProgressBar";
import { StatTile } from "./StatTile";
import { TextField } from "./TextField";

test("Button defaults to type=button with the touch target and focus ring", () => {
  render(<Button>Save</Button>);
  const button = screen.getByRole("button", { name: "Save" });
  expect(button).toHaveAttribute("type", "button");
  expect(button.className).toContain("min-h-touch");
  expect(button.className).toContain("focus-visible:shadow-focus");
});

test("TextField labels its input and links the error", () => {
  render(<TextField label="Monthly amount" suffix="HUF" error="Too much." hint="Whole forints." />);
  const input = screen.getByLabelText("Monthly amount");
  expect(input.className).toContain("min-h-touch");
  expect(input).toHaveAttribute("aria-invalid", "true");
  expect(input).toHaveAccessibleDescription("Too much. Whole forints.");
  expect(screen.getByText("HUF")).toBeInTheDocument();
});

test("Checkbox is labelled and reachable", () => {
  render(<Checkbox label="I have read the mandate" />);
  expect(screen.getByRole("checkbox", { name: "I have read the mandate" })).not.toBeChecked();
});

test("ErrorMessage shows Error and string messages, nothing for null", () => {
  const { rerender } = render(<ErrorMessage error={null} />);
  expect(screen.queryByRole("alert")).toBeNull();
  rerender(<ErrorMessage error={new Error("Plan not found.")} />);
  expect(screen.getByRole("alert")).toHaveTextContent("Plan not found.");
  rerender(<ErrorMessage error="Choose how much risk you accept." />);
  expect(screen.getByRole("alert")).toHaveTextContent("Choose how much risk you accept.");
});

test("badges map statuses and confidence to Figma tones", () => {
  expect(statusBadge("scheduled")).toEqual({ tone: "info", label: "Scheduled" });
  expect(statusBadge("executed")).toEqual({ tone: "success", label: "Done" });
  expect(statusBadge("awaiting_approval")).toEqual({ tone: "warning", label: "Needs approval" });
  expect(confidenceBadge("normal")).toEqual({ tone: "success", label: "High confidence" });
  expect(confidenceBadge("low")).toEqual({ tone: "warning", label: "Low confidence" });
  render(<Badge tone="success">Active</Badge>);
  expect(screen.getByText("Active")).toBeInTheDocument();
});

test("ProgressBar exposes its value", () => {
  render(<ProgressBar label="Emergency fund" percent={96} />);
  const bar = screen.getByRole("progressbar", { name: "Emergency fund" });
  expect(bar).toHaveAttribute("aria-valuenow", "96");
});

test("StatTile and Icon render", () => {
  render(
    <>
      <StatTile label="Median monthly surplus" value="105,000 HUF" caption="Last 6 complete months" />
      <Icon name="home" />
    </>,
  );
  expect(screen.getByText("105,000 HUF")).toBeInTheDocument();
  expect(document.querySelector("svg[aria-hidden='true']")).not.toBeNull();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/format.test.ts src/components src/theme`
Expected: FAIL with `Failed to resolve import "./format"` / `"./Badge"`. (`tokens.test.ts` passes already.)

- [ ] **Step 3: Write the tokens (Figma variables, verbatim)**

Replace `frontend/src/theme/theme.css`:

```css
@import "tailwindcss";

/*
 * Design tokens from the Figma file QUT5rnXj1U6BYjty7YH5uS (local variables `color`, `space`,
 * text styles, effect styles Focus/Ring and Elevation/Panel). Update values here only, from Figma.
 * `--color-*: initial` removes Tailwind's default palette, so only these colours exist.
 * Spacing: Tailwind's 4 px step equals Figma space-N (p-4 = space-4 = 16 px).
 */
@theme {
  --color-*: initial;
  --color-bg: #f5f7f8;
  --color-surface: #ffffff;
  --color-surface-hover: #f2f4f7;
  --color-text: #101828;
  --color-text-muted: #667085;
  --color-border: #e4e7ec;
  --color-border-strong: #98a2b3;
  --color-primary: #0f766e;
  --color-primary-hover: #115e59;
  --color-primary-subtle: #e6f4f1;
  --color-on-primary: #ffffff;
  --color-danger: #b42318;
  --color-danger-bg: #fef3f2;
  --color-success: #067647;
  --color-success-bg: #ecfdf3;
  --color-warning: #b54708;
  --color-warning-bg: #fffaeb;
  --color-info: #175cd3;
  --color-info-bg: #eff8ff;
  --color-focus-ring: #1d4ed8;
  --color-tooltip-bg: #101828;
  --color-chart-saved: #14b8a6;
  --color-chart-income: #cbd5e1;
  --color-chart-skipped: #f79009;
  --color-chart-grid: #eaecf0;

  --spacing: 4px;
  --spacing-touch: 44px; /* var(--target-min) */
  --spacing-sidebar: 248px;
  --spacing-panel: 360px; /* sticky summary panel */
  --spacing-content: 1040px;
  --spacing-narrow: 720px;
  /* max-w-* reads the container namespace: same widths as max-w-content / max-w-narrow. */
  --container-content: 1040px;
  --container-narrow: 720px;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 999px;

  --shadow-panel: 0 4px 16px 0 rgb(16 24 40 / 0.06); /* Elevation/Panel */
  --shadow-focus: 0 0 0 2px var(--color-surface), 0 0 0 4px var(--color-focus-ring); /* Focus/Ring */

  --font-sans: "Inter Variable", "Inter", system-ui, sans-serif;
  --text-h1: 28px;
  --text-h1--line-height: 36px;
  --text-h1--font-weight: 600;
  --text-h2: 20px;
  --text-h2--line-height: 28px;
  --text-h2--font-weight: 600;
  --text-h3: 16px;
  --text-h3--line-height: 24px;
  --text-h3--font-weight: 600;
  --text-body: 14px;
  --text-body--line-height: 20px;
  --text-caption: 12px;
  --text-caption--line-height: 16px;
  --text-caption--font-weight: 500;
  --text-number: 32px;
  --text-number--line-height: 40px;
  --text-number--font-weight: 700;
}

@layer base {
  body {
    background-color: var(--color-bg);
    color: var(--color-text);
    font-family: var(--font-sans);
    font-size: var(--text-body);
    line-height: var(--text-body--line-height);
  }
}
```

The `rgb(16 24 40 / 0.06)` is `#1018280F` from Elevation/Panel, written as `rgb()` because `theme.css` is the one place raw values live (the guard scans `.ts`/`.tsx` only).

In `frontend/src/main.tsx`, add `import "@fontsource-variable/inter";` as the first line.

- [ ] **Step 4: Implement formatting**

`frontend/src/format.ts`:

```ts
/**
 * Display and input helpers. They format values from the API and parse customer input;
 * they never compute money or dates (golden rule 2).
 */
import type { Huf } from "./api/types";

const thousands = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export const AMOUNT_HINT = "Whole forints. Cannot be negative.";

/** 1220000 → "1,220,000". */
export function formatNumber(amount: Huf): string {
  return thousands.format(amount);
}

/** 73500 → "73,500 HUF", the same format as the backend explanation templates. */
export function formatHuf(amount: Huf): string {
  return `${formatNumber(amount)} HUF`;
}

/** Transaction amounts on Home: "+550,000 HUF", "−150,000 HUF" (typographic minus, Figma 02). */
export function formatSigned(amount: Huf): string {
  if (amount > 0) return `+${formatHuf(amount)}`;
  if (amount < 0) return `−${formatNumber(Math.abs(amount))} HUF`;
  return formatHuf(amount);
}

/** "2026-09-01" → "2026-09". String slicing, so no time-zone shift. */
export function formatMonth(iso: string): string {
  return iso.slice(0, 7);
}

/** "2026-10-06T10:00:00Z" → "2026-10-06". */
export function formatDay(iso: string): string {
  return iso.slice(0, 10);
}

/** "2025-12-01" → "Dec" (chart axis). */
export function monthName(iso: string): string {
  return MONTHS[Number(iso.slice(5, 7)) - 1] ?? iso.slice(5, 7);
}

/** "2025-12-01" → "2025". */
export function monthYear(iso: string): string {
  return iso.slice(0, 4);
}

/** "anna" → "Anna" (greeting and sidebar). */
export function displayName(username: string): string {
  return username.charAt(0).toUpperCase() + username.slice(1);
}

/**
 * A whole, non-negative forint amount typed by the customer. Spaces and thousands commas are
 * allowed ("250 000", "250,000"). Decimals, signs, exponents and empty text give null.
 */
export function parseHuf(text: string): Huf | null {
  const digits = text.replace(/[\s,]/g, "");
  if (!/^\d+$/.test(digits)) return null;
  const value = Number(digits);
  return Number.isSafeInteger(value) ? value : null;
}
```

`Math.abs` in `formatSigned` only changes how a backend amount is printed, never a value that is used or sent; it is the one allowed use.

- [ ] **Step 5: Implement the components**

`frontend/src/components/Icon.tsx`:

```tsx
/** The Figma Icon/* set (frame 2:5), 20 px, 1.75 px stroke, currentColor. Decorative: the
 * control around it carries the accessible name. */
const PATHS = {
  home: ["M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"],
  savings: ["M22 7 13.5 15.5l-5-5L2 17", "M16 7h6v6"],
  activity: ["M22 12h-4l-3 9L9 3l-3 9H2"],
  profile: ["M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2", "M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"],
  alert: ["M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z", "M12 9v4", "M12 17h.01"],
  "arrow-left": ["M19 12H5", "m12 19-7-7 7-7"],
  check: ["M20 6 9 17l-5-5"],
  "chevron-down": ["m6 9 6 6 6-6"],
  "chevron-right": ["m9 18 6-6-6-6"],
  close: ["M18 6 6 18", "m6 6 12 12"],
  history: ["M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8", "M3 3v5h5", "M12 7v5l4 2"],
  info: ["M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z", "M12 16v-4", "M12 8h.01"],
  lock: ["M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z", "M7 11V7a5 5 0 0 1 10 0v4"],
  "log-out": ["M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", "m16 17 5-5-5-5", "M21 12H9"],
  menu: ["M4 6h16", "M4 12h16", "M4 18h16"],
  enter: ["m9 10-5 5 5 5", "M20 4v7a4 4 0 0 1-4 4H4"],
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, className = "size-5" }: { name: IconName; className?: string }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`shrink-0 ${className}`}
    >
      {PATHS[name].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
```

`frontend/src/components/Button.tsx`:

```tsx
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
export function Button({ variant = "primary", className = "", type = "button", ...props }: ButtonProps) {
  return <button type={type} className={`${buttonClass(variant)} ${className}`} {...props} />;
}
```

`frontend/src/components/Badge.tsx`:

```tsx
import type { ReactNode } from "react";
import type { ActivityStatus, Confidence } from "../api/types";

export type BadgeTone = "success" | "warning" | "info" | "neutral";

const TONES: Record<BadgeTone, string> = {
  success: "bg-success-bg text-success",
  warning: "bg-warning-bg text-warning",
  info: "bg-info-bg text-info",
  neutral: "bg-surface-hover text-text",
};

/** Figma Badges (frame 2:180): a dot and a short label. */
export function Badge({ tone, children }: { tone: BadgeTone; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-caption ${TONES[tone]}`}>
      <span aria-hidden="true" className="size-1.5 rounded-full bg-current" />
      {children}
    </span>
  );
}

const STATUS: Record<ActivityStatus, { tone: BadgeTone; label: string }> = {
  scheduled: { tone: "info", label: "Scheduled" },
  executed: { tone: "success", label: "Done" },
  done: { tone: "success", label: "Done" },
  awaiting_approval: { tone: "warning", label: "Needs approval" },
  denied: { tone: "warning", label: "Skipped" },
  proposed: { tone: "neutral", label: "Proposed" },
  rejected: { tone: "neutral", label: "Rejected" },
  paused: { tone: "warning", label: "Paused" },
};

export function statusBadge(status: ActivityStatus): { tone: BadgeTone; label: string } {
  return STATUS[status];
}

const CONFIDENCE: Record<Confidence, { tone: BadgeTone; label: string }> = {
  normal: { tone: "success", label: "High confidence" },
  low: { tone: "warning", label: "Low confidence" },
  none: { tone: "warning", label: "Your own estimate" },
};

export function confidenceBadge(confidence: Confidence): { tone: BadgeTone; label: string } {
  return CONFIDENCE[confidence];
}
```

`frontend/src/components/TextField.tsx`:

```tsx
import { useId, type InputHTMLAttributes } from "react";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
  error?: string | null;
  suffix?: string;
}

/** Figma Input (frame 2:182): label, 44 px input, optional suffix ("HUF"), error then hint. */
export function TextField({ label, hint, error, suffix, className = "", id, ...props }: TextFieldProps) {
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
```

`frontend/src/components/Checkbox.tsx`:

```tsx
import type { InputHTMLAttributes } from "react";

/** Figma Checkbox (frame 2:182): the whole row is the 44 px target. */
export function Checkbox({ label, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex min-h-touch cursor-pointer items-center gap-3 rounded-md px-3 hover:bg-surface-hover">
      <input type="checkbox" className="size-5 accent-primary outline-none focus-visible:shadow-focus" {...props} />
      <span className="text-body">{label}</span>
    </label>
  );
}
```

`frontend/src/components/ErrorMessage.tsx`:

```tsx
/** Shows an Error's message (API errors carry the backend's detail text) or a string. */
export function ErrorMessage({ error }: { error: unknown }) {
  if (error === null || error === undefined || error === "") return null;
  const text =
    typeof error === "string" ? error : error instanceof Error ? error.message : "Something went wrong.";
  return (
    <p role="alert" className="rounded-md border border-danger bg-danger-bg p-3 text-body text-danger">
      {text}
    </p>
  );
}
```

`frontend/src/components/Card.tsx`:

```tsx
import type { ReactNode } from "react";

/** White card, radius-lg, border (every Figma content block). */
export function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-lg border border-border bg-surface p-6 ${className}`}>
      {title ? <h2 className="mb-4 text-h3">{title}</h2> : null}
      {children}
    </section>
  );
}
```

`frontend/src/components/StatTile.tsx`:

```tsx
/** Figma StatTile (frame 3:191): label, big value, optional caption. */
export function StatTile({ label, value, caption }: { label: string; value: string; caption?: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <p className="text-caption text-text-muted">{label}</p>
      <p className="mt-1 text-h1">{value}</p>
      {caption ? <p className="mt-1 text-caption text-text-muted">{caption}</p> : null}
    </div>
  );
}
```

`frontend/src/components/Kbd.tsx`:

```tsx
import type { ReactNode } from "react";

/** Keyboard hint chip ("Tab", "Enter ↵") from Figma 03, 07b, 10. */
export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="rounded-sm border border-border-strong bg-surface px-1.5 py-0.5 font-sans text-caption">
      {children}
    </kbd>
  );
}
```

`frontend/src/components/ProgressBar.tsx`:

```tsx
/** Home "Your savings plan" bars. `percent` comes from the API (progress_percent). */
export function ProgressBar({ label, percent }: { label: string; percent: number }) {
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      className="h-1.5 w-full rounded-full bg-surface-hover"
    >
      <div className="h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
    </div>
  );
}
```

The inline `style` width is the one dynamic value; it is not a hex colour or a Tailwind arbitrary class.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass. If `toHaveAccessibleDescription` gives the parts in another order, keep the error before the hint (`describedBy` order) and fix the component, not the test.

- [ ] **Step 7: Lint, docs**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend design tokens copied from the Figma variables (colours, spacing, radii, Focus/Ring, Elevation/Panel, text styles, Inter) and base components: Icon, Button, Badge, TextField, Checkbox, ErrorMessage, Card, StatTile, Kbd, ProgressBar (44 px targets, labelled controls, visible focus).
```

Tick in `docs/tasks.md`: "Theme tokens in `src/theme/` (from Figma variables if available)."

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): figma design tokens, formatting and base components`

---

### Task 8: Layout components: SideNav, AppShell, FlowHeader, FlowLayout, SummaryPanel, Modal

Deliverable: the two Figma layouts and the overlays, responsive as the `Responsive & interaction notes` frame (`10:1074`) says. Figma: `Navigation` (`3:3`), `Flow header (focused layout)` (`3:79`), `Sticky summary panel` (`3:261`), `Overlays` (`2:236`), 375 px frames `10:906`, `10:981`.

**Files:**
- Create: `frontend/src/components/{SideNav,AppShell,FlowHeader,FlowLayout,SummaryPanel,Modal}.tsx`, `frontend/src/components/layout.test.tsx`
- Modify: `CHANGELOG.md`, `docs/tasks.md`

**Interfaces:**
- Consumes: `Icon`, `Badge`, `Button`, `buttonClass` (Task 7), `Me` (Task 6), `displayName` (Task 7), React Router `NavLink`, `Link`.
- Produces:
  - `SideNav({ user: Me, onLogout: () => void, onNavigate?: () => void })` — `<nav aria-label="Main">` with links Home `/`, Savings plan `/plan`, Activity `/activity`; "Simulated bank data" badge; user block; "Log out" button.
  - `AppShell({ user: Me, onLogout: () => void, children })` — sidebar from 1024 px; below it a top bar with a "Open menu" button (`aria-expanded`, `aria-controls="drawer"`) and the drawer (Esc or a link closes it).
  - `FlowHeader({ step: 1 | 2 | 3 | 4, title: string, backTo: string | null })` — Back link, "Step N of 4" + title + 4-segment progress (`role="progressbar"`, `aria-valuenow=step`, `aria-valuemax=4`), "Save & exit" link to `/`.
  - `FlowLayout({ step, title, backTo, children, wide? })` — `FlowHeader` + `<main>`.
  - `SummaryPanel({ label: string, value: ReactNode, badge?: ReactNode, details?: ReactNode, action: ReactNode, note?: string })` — `<aside aria-label="Summary">`: sticky 360 px card from 1024 px, a fixed bottom bar below (details hidden). Rendered once, so its button exists once in the DOM.
  - `Modal({ title: string, icon?: IconName, onClose: () => void, children })` — `role="dialog"`, `aria-modal`, labelled by the title; Esc closes; focus moves to the first field and is trapped; focus returns on close.

- [ ] **Step 1: Write the failing tests**

`frontend/src/components/layout.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { expect, test, vi } from "vitest";
import { AppShell } from "./AppShell";
import { Button } from "./Button";
import { FlowHeader } from "./FlowHeader";
import { Modal } from "./Modal";
import { SideNav } from "./SideNav";
import { SummaryPanel } from "./SummaryPanel";

const ANNA = { username: "anna", role: "customer" as const };

test("SideNav marks the current page and shows the user", () => {
  render(
    <MemoryRouter initialEntries={["/plan"]}>
      <SideNav user={ANNA} onLogout={vi.fn()} />
    </MemoryRouter>,
  );
  expect(screen.getByRole("link", { name: "Savings plan" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByRole("link", { name: "Home" })).not.toHaveAttribute("aria-current");
  expect(screen.getByText("Anna")).toBeInTheDocument();
  expect(screen.getByText("Simulated bank data")).toBeInTheDocument();
});

test("SideNav logs out", async () => {
  const onLogout = vi.fn();
  render(
    <MemoryRouter>
      <SideNav user={ANNA} onLogout={onLogout} />
    </MemoryRouter>,
  );
  await userEvent.setup().click(screen.getByRole("button", { name: "Log out" }));
  expect(onLogout).toHaveBeenCalledOnce();
});

test("AppShell menu button opens and Esc closes the drawer", async () => {
  render(
    <MemoryRouter>
      <AppShell user={ANNA} onLogout={vi.fn()}>
        <p>Content</p>
      </AppShell>
    </MemoryRouter>,
  );
  const user = userEvent.setup();
  const menu = screen.getByRole("button", { name: "Open menu" });
  expect(menu).toHaveAttribute("aria-expanded", "false");
  await user.click(menu);
  expect(menu).toHaveAttribute("aria-expanded", "true");
  expect(document.getElementById("drawer")).not.toBeNull();
  await user.keyboard("{Escape}");
  expect(menu).toHaveAttribute("aria-expanded", "false");
});

test("FlowHeader shows the step, back and exit", () => {
  render(
    <MemoryRouter>
      <FlowHeader step={3} title="Plan review" backTo="/plans/7/analysis" />
    </MemoryRouter>,
  );
  expect(screen.getByText("Step 3 of 4")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Back" })).toHaveAttribute("href", "/plans/7/analysis");
  expect(screen.getByRole("link", { name: "Save & exit" })).toHaveAttribute("href", "/");
  expect(screen.getByRole("progressbar", { name: "Plan steps" })).toHaveAttribute("aria-valuenow", "3");
});

test("SummaryPanel renders its action once", () => {
  render(
    <SummaryPanel label="Monthly amount" value="73,500 HUF" details={<p>Details</p>} action={<Button>Continue to mandate</Button>} />,
  );
  expect(screen.getAllByRole("button", { name: "Continue to mandate" })).toHaveLength(1);
  expect(screen.getByRole("complementary", { name: "Summary" })).toBeInTheDocument();
});

test("Modal focuses its field, traps Tab and closes on Esc", async () => {
  const onClose = vi.fn();
  render(
    <>
      <button type="button">Outside</button>
      <Modal title="Confirm with your password" onClose={onClose}>
        <label>
          Password
          <input type="password" />
        </label>
        <button type="button">Confirm and sign</button>
      </Modal>
    </>,
  );
  const user = userEvent.setup();
  expect(screen.getByRole("dialog", { name: "Confirm with your password" })).toHaveAttribute("aria-modal", "true");
  expect(screen.getByLabelText("Password")).toHaveFocus();
  await user.tab(); // Confirm and sign
  await user.tab(); // Close (×)
  await user.tab(); // wraps to the field, never "Outside"
  expect(screen.getByLabelText("Password")).toHaveFocus();
  await user.keyboard("{Escape}");
  expect(onClose).toHaveBeenCalledOnce();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/components/layout.test.tsx`
Expected: FAIL with `Failed to resolve import "./AppShell"`.

- [ ] **Step 3: Implement SideNav and AppShell**

`frontend/src/components/SideNav.tsx`:

```tsx
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
export function SideNav({ user, onLogout, onNavigate }: { user: Me; onLogout: () => void; onNavigate?: () => void }) {
  const name = displayName(user.username);
  return (
    <div className="flex h-full w-sidebar flex-col border-r border-border bg-surface p-4">
      <p className="flex items-center gap-2 px-2 py-3 text-h3">
        <span aria-hidden="true" className="flex size-8 items-center justify-center rounded-md bg-primary text-on-primary">
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
          <span aria-hidden="true" className="flex size-8 items-center justify-center rounded-full bg-primary-subtle text-primary">
            {name.charAt(0)}
          </span>
          <div>
            <p className="text-body font-semibold">{name}</p>
            <p className="text-caption text-text-muted">{user.role === "admin" ? "Admin" : "Customer"}</p>
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
```

`frontend/src/components/AppShell.tsx`:

```tsx
import { useEffect, useState, type ReactNode } from "react";
import type { Me } from "../api/types";
import { Icon } from "./Icon";
import { SideNav } from "./SideNav";

/** Sidebar layout (Figma 02, 08). Below 1024 px: top bar + drawer (Figma 10:906). */
export function AppShell({ user, onLogout, children }: { user: Me; onLogout: () => void; children: ReactNode }) {
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
          <div aria-hidden="true" className="absolute inset-0 bg-text/50" onClick={() => setOpen(false)} />
          <div id="drawer" className="relative h-full w-sidebar">
            <SideNav user={user} onLogout={onLogout} onNavigate={() => setOpen(false)} />
          </div>
        </div>
      ) : null}
      <main className="mx-auto w-full max-w-content flex-1 px-4 py-8 lg:px-8">{children}</main>
    </div>
  );
}
```

- [ ] **Step 4: Implement FlowHeader and FlowLayout**

`frontend/src/components/FlowHeader.tsx`:

```tsx
import { Link } from "react-router";
import { buttonClass } from "./Button";
import { Icon } from "./Icon";

const STEPS = [1, 2, 3, 4] as const;

/** Figma FlowHeader (frame 3:79): plan flow without sidebar. Compact below 768 px (10:982). */
export function FlowHeader({ step, title, backTo }: { step: 1 | 2 | 3 | 4; title: string; backTo: string | null }) {
  return (
    <header className="flex h-14 items-center justify-between gap-4 border-b border-border bg-surface px-4 md:h-18 md:px-6">
      <div className="flex items-center gap-4">
        <p className="hidden items-center gap-2 text-h3 md:flex">
          <span aria-hidden="true" className="flex size-8 items-center justify-center rounded-md bg-primary text-on-primary">
            S
          </span>
          SaverAI
        </p>
        {backTo ? (
          <Link to={backTo} aria-label="Back" className={buttonClass("ghost")}>
            <Icon name="arrow-left" />
            <span className="hidden md:inline">Back</span>
          </Link>
        ) : null}
      </div>
      <div className="text-center">
        <p className="text-caption text-text-muted">
          Step {step} of 4 <span className="hidden font-semibold text-text md:inline">{title}</span>
        </p>
        <div
          role="progressbar"
          aria-label="Plan steps"
          aria-valuemin={1}
          aria-valuemax={4}
          aria-valuenow={step}
          className="mt-1 flex gap-1"
        >
          {STEPS.map((n) => (
            <span key={n} className={`h-1 w-9 rounded-full ${n <= step ? "bg-primary" : "bg-border"}`} />
          ))}
        </div>
      </div>
      <Link to="/" className={buttonClass("secondary")}>
        Save &amp; exit
      </Link>
    </header>
  );
}
```

The back link keeps `aria-label="Back"` because its text is hidden below 768 px (icon only, Figma 10:982).

`frontend/src/components/FlowLayout.tsx`:

```tsx
import type { ReactNode } from "react";
import { FlowHeader } from "./FlowHeader";

interface FlowLayoutProps {
  step: 1 | 2 | 3 | 4;
  title: string;
  backTo: string | null;
  children: ReactNode;
  /** Two-column screens (plan review, mandate) use the full 1040 px; forms use 720 px. */
  wide?: boolean;
}

export function FlowLayout({ step, title, backTo, children, wide = false }: FlowLayoutProps) {
  return (
    <div className="min-h-screen">
      <FlowHeader step={step} title={title} backTo={backTo} />
      <main className={`mx-auto w-full px-4 pt-8 pb-32 lg:pb-12 ${wide ? "max-w-content" : "max-w-narrow"}`}>
        {children}
      </main>
    </div>
  );
}
```

- [ ] **Step 5: Implement SummaryPanel and Modal**

`frontend/src/components/SummaryPanel.tsx`:

```tsx
import type { ReactNode } from "react";

interface SummaryPanelProps {
  label: string;
  value: ReactNode;
  badge?: ReactNode;
  details?: ReactNode;
  action: ReactNode;
  note?: string;
}

/**
 * Figma "Sticky summary panel" (3:261): from 1024 px a 360 px card, position sticky, top 24 px;
 * below 1024 px a fixed bottom action bar with the value, the badge and the main button
 * (details and note hidden). One DOM tree, so the action exists once.
 */
export function SummaryPanel({ label, value, badge, details, action, note }: SummaryPanelProps) {
  return (
    <aside
      aria-label="Summary"
      className="fixed inset-x-0 bottom-0 z-30 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-border bg-surface p-4 shadow-panel lg:sticky lg:top-6 lg:block lg:w-panel lg:shrink-0 lg:self-start lg:rounded-lg lg:border lg:p-6"
    >
      <div className="flex w-full items-center justify-between gap-3">
        <p className="text-caption text-text-muted">{label}</p>
        {badge}
      </div>
      <div className="flex-1 text-h2 lg:mt-1 lg:text-number">{value}</div>
      {details ? <div className="mt-4 hidden space-y-3 border-t border-border pt-4 lg:block">{details}</div> : null}
      <div className="lg:mt-4 lg:grid">{action}</div>
      {note ? <p className="mt-3 hidden text-center text-caption text-text-muted lg:block">{note}</p> : null}
    </aside>
  );
}
```

`lg:grid` makes the button full width in the panel; in the bar it sits right of the value.

`frontend/src/components/Modal.tsx`:

```tsx
import { useEffect, useId, useRef, type KeyboardEvent, type ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

const FOCUSABLE = 'input, button, a[href], select, textarea, [tabindex]:not([tabindex="-1"])';

/** Figma Modal (frame 2:236, 07b): centred, scrim 50 %, focus trapped, Esc closes. */
export function Modal({ title, icon, onClose, children }: { title: string; icon?: IconName; onClose: () => void; children: ReactNode }) {
  const titleId = useId();
  const dialog = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const first = dialog.current?.querySelector<HTMLElement>("input") ?? dialog.current?.querySelector<HTMLElement>(FOCUSABLE);
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
    const items = [...dialog.current.querySelectorAll<HTMLElement>(FOCUSABLE)].filter((el) => !el.hasAttribute("disabled"));
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
```

`max-w-120` is the 4 px scale (480 px, the Figma modal width), not an arbitrary value. `items.length - 1` is index arithmetic, not money.

The DOM order inside the dialog is title, close button, children; the test tabs field → "Confirm and sign" → wraps. Adjust the test comment if your DOM order differs, but keep the assertion that focus never leaves the dialog.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass. If the Modal test fails on tab order, print `document.activeElement?.outerHTML` after each tab; the trap must keep focus inside the dialog (fix the component).

- [ ] **Step 7: Lint, docs**

`CHANGELOG.md`, `### Added`: `- Frontend layouts from Figma: SideNav and AppShell (drawer below 1024 px), FlowHeader / FlowLayout (Step N of 4, Back, Save & exit), sticky SummaryPanel (bottom bar below 1024 px) and an accessible Modal (focus trap, Esc).`

Tick in `docs/tasks.md`: "Shared components: Button, TransactionRow, SideNav (44 px touch targets, accessible labels)." only after Task 10 adds `TransactionRow`; leave it for now.

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): app shell, flow layout, summary panel and modal from figma`

---

### Task 9: Login (01), protected routing and the customer layout

Deliverable: the router, the Figma 01 login screen (brand panel + form), a guard that sends logged-out customers or expired sessions to `/login`, and the customer layout (`AppShell`) around Home, Savings plan and Activity. Figma: `5:73`.

**Files:**
- Create: `frontend/src/api/hooks.ts`, `frontend/src/screens/login/LoginScreen.tsx`
- Modify: `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `frontend/src/main.tsx`, `frontend/src/test/render.tsx`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `apiFetch`, `ApiError`, `makeQueryClient` (Task 6), `TextField`, `Button`, `ErrorMessage`, `Icon` (Task 7), `AppShell` (Task 8), `/api/auth/me|login|logout` (existing backend).
- Produces:
  - `hooks.ts`: `keys` (`me`, `account`, `rules`, `analysis`, `plans`, `plan(id)`, `timeMachine(id)`, `mandate(id)`, `activePlan`, `activity`), `orNull<T>(request, status)`, `useMe()` (data `Me | null`), `useLogin()`, `useLogout()`.
  - `App.tsx`: `App`, `createQueryClient()` (401 anywhere → `me` = null → redirect), `CustomerLayout` (AppShell + `<Outlet />`); routes `/login`; inside the guard: layout routes `/` (placeholder until Task 10), `/plan`, `/activity` (placeholders until Task 17) and flow routes added by Tasks 11–16.
  - `render.tsx`: `renderApp(url: string): QueryClient`.

- [ ] **Step 1: Write the failing tests**

Replace `frontend/src/App.test.tsx`:

```tsx
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { apiFetch } from "./api/client";
import { mockApi, renderApp } from "./test/render";

const ANNA = { username: "anna", role: "customer" };
const LOGGED_OUT = { status: 401, body: { detail: "Unauthorized" } };

test("a logged-out visitor is sent to the login screen", async () => {
  mockApi({ "GET /api/auth/me": LOGGED_OUT });
  renderApp("/");
  expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
  expect(screen.getByText(/Demo only/)).toBeInTheDocument();
});

test("logging in opens the customer layout", async () => {
  let loggedIn = false;
  const calls = mockApi({
    "GET /api/auth/me": () => (loggedIn ? { body: ANNA } : LOGGED_OUT),
    "POST /api/auth/login": () => {
      loggedIn = true;
      return { body: ANNA };
    },
  });
  renderApp("/login");
  const user = userEvent.setup();
  await user.type(await screen.findByLabelText("Username"), "anna");
  await user.type(screen.getByLabelText("Password"), "secret");
  await user.click(screen.getByRole("button", { name: "Log in" }));
  expect(await screen.findByRole("navigation", { name: "Main" })).toBeInTheDocument();
  expect(calls.find((call) => call.method === "POST")?.body).toEqual({ username: "anna", password: "secret" });
});

test("a wrong password shows the backend message", async () => {
  mockApi({
    "GET /api/auth/me": LOGGED_OUT,
    "POST /api/auth/login": { status: 401, body: { detail: "Invalid username or password." } },
  });
  renderApp("/login");
  const user = userEvent.setup();
  await user.type(await screen.findByLabelText("Username"), "anna");
  await user.type(screen.getByLabelText("Password"), "wrong");
  await user.click(screen.getByRole("button", { name: "Log in" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Invalid username or password.");
});

test("an expired session mid-flow returns to login", async () => {
  mockApi({ "GET /api/auth/me": { body: ANNA }, "GET /api/plans/7": LOGGED_OUT });
  const queryClient = renderApp("/");
  await screen.findByRole("navigation", { name: "Main" });
  await queryClient
    .fetchQuery({ queryKey: ["plans", 7], queryFn: () => apiFetch("/api/plans/7") })
    .catch(() => undefined);
  expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
});

test("logging out returns to login", async () => {
  mockApi({ "GET /api/auth/me": { body: ANNA }, "POST /api/auth/logout": { body: { ok: true } } });
  renderApp("/");
  await userEvent.setup().click(await screen.findByRole("button", { name: "Log out" }));
  expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
});

test("an unknown URL goes to home", async () => {
  mockApi({ "GET /api/auth/me": { body: ANNA } });
  renderApp("/nope");
  expect(await screen.findByRole("navigation", { name: "Main" })).toBeInTheDocument();
});
```

Append to `frontend/src/test/render.tsx` and add `import { App, createQueryClient } from "../App";` at the top:

```tsx
/** Render the whole app (router, login guard, 401 handling) at `url`. */
export function renderApp(url: string): QueryClient {
  const queryClient = createQueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return queryClient;
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/App.test.tsx`
Expected: FAIL — `createQueryClient` is not exported.

- [ ] **Step 3: Implement the hooks**

`frontend/src/api/hooks.ts`:

```ts
/** TanStack Query hooks: one per endpoint. Screens never call apiFetch directly. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiFetch } from "./client";
import type { LoginIn, Me } from "./types";

export const keys = {
  me: ["me"],
  account: ["account"],
  rules: ["rules"],
  analysis: ["analysis"],
  plans: ["plans"],
  plan: (id: number) => ["plans", id],
  timeMachine: (id: number) => ["plans", id, "time-machine"],
  mandate: (id: number) => ["plans", id, "mandate"],
  activePlan: ["plans", "active"],
  activity: ["activity"],
} as const;

/** Resolve to null instead of failing when the API answers with `status` (e.g. 401, 404). */
export async function orNull<T>(request: Promise<T>, status: number): Promise<T | null> {
  try {
    return await request;
  } catch (error) {
    if (error instanceof ApiError && error.status === status) return null;
    throw error;
  }
}

/** The logged-in user, or null when logged out. */
export function useMe() {
  return useQuery({ queryKey: keys.me, queryFn: () => orNull(apiFetch<Me>("/api/auth/me"), 401) });
}

export function useLogin() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (credentials: LoginIn) => apiFetch<Me>("/api/auth/login", { method: "POST", body: credentials }),
    onSuccess: (me) => {
      client.setQueryData(keys.me, me);
    },
  });
}

export function useLogout() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
    onSettled: () => {
      client.clear();
      client.setQueryData(keys.me, null);
    },
  });
}
```

- [ ] **Step 4: Implement the login screen (Figma 01)**

`frontend/src/screens/login/LoginScreen.tsx`:

```tsx
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useLogin } from "../../api/hooks";
import { Button } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Icon } from "../../components/Icon";
import { TextField } from "../../components/TextField";

const POINTS = [
  "Fixed, transparent rules",
  "Financial time machine on your own history",
  "Orders run only under a mandate you sign",
];

/** Figma 01 Login (5:73): brand panel (hidden below 1024 px) and form. */
export function LoginScreen() {
  const login = useLogin();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    login.mutate({ username, password }, { onSuccess: () => navigate("/") });
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="hidden flex-col justify-center gap-6 bg-primary p-16 text-on-primary lg:flex">
        <p className="text-h2">SaverAI</p>
        <h2 className="text-number">Save what you already don&apos;t spend.</h2>
        <p className="max-w-narrow text-h3 font-normal">
          SaverAI looks at your past months, suggests a monthly amount and replays it on your own history
          before anything runs.
        </p>
        <ul className="space-y-3">
          {POINTS.map((point) => (
            <li key={point} className="flex items-center gap-3">
              <Icon name="check" />
              {point}
            </li>
          ))}
        </ul>
      </section>
      <main className="flex items-center justify-center bg-surface px-4">
        <form className="w-full max-w-100 space-y-5" onSubmit={submit}>
          <h1 className="text-h1">Log in</h1>
          <p className="text-text-muted">Use a demo persona, e.g. anna.</p>
          <TextField label="Username" autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} />
          <TextField
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <ErrorMessage error={login.error} />
          <Button type="submit" className="w-full" disabled={login.isPending}>
            Log in
            <Icon name="chevron-right" />
          </Button>
          <p className="text-caption text-text-muted">
            Demo only. Transactions, products and orders are simulated; no real bank is connected.
          </p>
        </form>
      </main>
    </div>
  );
}
```

- [ ] **Step 5: Implement the router, layout and app query client**

Replace `frontend/src/App.tsx`:

```tsx
import type { QueryClient } from "@tanstack/react-query";
import { Navigate, Outlet, Route, Routes, useNavigate } from "react-router";
import { keys, useLogout, useMe } from "./api/hooks";
import { makeQueryClient } from "./api/queryClient";
import { AppShell } from "./components/AppShell";
import { ErrorMessage } from "./components/ErrorMessage";
import { LoginScreen } from "./screens/login/LoginScreen";

/** Any 401 (expired session) clears the user, so RequireLogin redirects to /login. */
export function createQueryClient(): QueryClient {
  const client: QueryClient = makeQueryClient(() => client.setQueryData(keys.me, null));
  return client;
}

function RequireLogin() {
  const me = useMe();
  if (me.isPending) return <p className="p-4">Loading…</p>;
  if (me.isError) return <ErrorMessage error={me.error} />;
  return me.data === null ? <Navigate to="/login" replace /> : <Outlet />;
}

/** Home, Savings plan and Activity share the sidebar layout (Figma 02, 08). */
export function CustomerLayout() {
  const me = useMe();
  const logout = useLogout();
  const navigate = useNavigate();
  if (!me.data) return null;
  return (
    <AppShell user={me.data} onLogout={() => logout.mutate(undefined, { onSettled: () => navigate("/login") })}>
      <Outlet />
    </AppShell>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginScreen />} />
      <Route element={<RequireLogin />}>
        <Route element={<CustomerLayout />}>
          {/* Task 10 replaces "/" with HomeScreen; Task 17 replaces "/plan" and "/activity". */}
          <Route path="/" element={<h1 className="text-h1">Home</h1>} />
          <Route path="/plan" element={<h1 className="text-h1">Your savings plan</h1>} />
          <Route path="/activity" element={<h1 className="text-h1">Activity</h1>} />
        </Route>
        {/* Flow routes (Tasks 11–16) go here: they render FlowLayout themselves. */}
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
```

Replace `frontend/src/main.tsx`:

```tsx
import "@fontsource-variable/inter";
import "./theme/theme.css";
import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import { App, createQueryClient } from "./App";

const queryClient = createQueryClient();

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass (6 App tests). `getByRole("navigation", { name: "Main" })` may find two navs once the drawer is open; in these tests it is closed, so one.

- [ ] **Step 7: Lint, changelog**

`CHANGELOG.md`, `### Added`: `- Frontend login screen (Figma 01), protected routes and the sidebar layout; an expired session (401) returns the customer to login.`

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): login screen, protected routing and customer layout`

---

### Task 10: Home (02) with TransactionRow

Deliverable: Figma 02 Home (`5:118`, 375 px `10:906`): greeting with the server date, balance card (median surplus, minimum balance, next transfer), savings plan card with progress bars from the API, the 5 newest transactions, and the rule summary from `GET /api/rules`. Without an active plan: a "Start a savings plan" link.

**Files:**
- Create: `frontend/src/components/TransactionRow.tsx`, `frontend/src/screens/home/HomeScreen.tsx`, `frontend/src/screens/home/HomeScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `frontend/src/components/components.test.tsx`, `CHANGELOG.md`, `docs/tasks.md`

**Interfaces:**
- Consumes: `GET /api/account`, `GET /api/rules`, `GET /api/analysis`, `GET /api/plans/active` (404 = none), `GET /api/auth/me`; `keys`, `orNull`, `useMe` (Task 9); `Card`, `Badge`, `ProgressBar`, `buttonClass`, `Icon`, `ErrorMessage` (Task 7); `formatHuf`, `formatNumber`, `formatSigned`, `displayName` (Task 7); fixtures `PLAN`, `plan()`, `ANALYSIS` (Task 6).
- Produces: `useAccount()`, `useRules()`, `useAnalysis()`, `useActivePlan()` (data `PlanOut | null`); `TransactionRow({ transaction })`; `HomeScreen` at `/`.

- [ ] **Step 1: Write the failing tests**

Append to `frontend/src/components/components.test.tsx` (add the import `import { TransactionRow } from "./TransactionRow";`):

```tsx
test("TransactionRow signs amounts and explains own transfers", () => {
  render(
    <ul>
      <TransactionRow transaction={{ id: 1, booked_on: "2026-09-10", amount: 550_000, description: "Salary", own_transfer: false }} />
      <TransactionRow
        transaction={{ id: 2, booked_on: "2026-09-25", amount: -30_000, description: "To own savings account", own_transfer: true }}
      />
    </ul>,
  );
  expect(screen.getByText("+550,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("−30,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("2026-09-25 · Own transfer, ignored in surplus")).toBeInTheDocument();
});
```

`frontend/src/screens/home/HomeScreen.test.tsx`:

```tsx
import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import type { AccountOut } from "../../api/types";
import { ANALYSIS, PLAN, plan } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { HomeScreen } from "./HomeScreen";

const ACCOUNT: AccountOut = {
  today: "2026-10-08",
  name: "Main account",
  balance: 1_220_000,
  min_balance: 100_000,
  transactions: [{ id: 1, booked_on: "2026-10-03", amount: -150_000, description: "Rent", own_transfer: false }],
};
const RULES = { lines: ["Monthly amount = 70% of your median monthly surplus (last 6 months)."] };

function start(active: unknown) {
  mockApi({
    "GET /api/auth/me": { body: { username: "anna", role: "customer" } },
    "GET /api/account": { body: ACCOUNT },
    "GET /api/rules": { body: RULES },
    "GET /api/analysis": { body: ANALYSIS },
    "GET /api/plans/active": active === null ? { status: 404, body: { detail: "No active plan." } } : { body: active },
  });
  renderScreen(<HomeScreen />);
}

test("greets with the server date and shows the balance card", async () => {
  start(plan({ status: "accepted", mandate_version: 1 }));
  expect(await screen.findByRole("heading", { name: "Hello, Anna" })).toBeInTheDocument();
  expect(screen.getByText("Here is where your money stands today, 2026-10-08.")).toBeInTheDocument();
  expect(screen.getByText("1,220,000")).toBeInTheDocument();
  expect(screen.getByText("105,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("100,000 HUF")).toBeInTheDocument();
  expect(await screen.findByText("2026-11-01")).toBeInTheDocument();
});

test("shows the plan with progress from the API", async () => {
  start(plan({ status: "accepted", mandate_version: 1 }));
  const card = (await screen.findByRole("heading", { name: "Your savings plan" })).closest("section");
  if (card === null) throw new Error("no plan card");
  const inCard = within(card);
  expect(inCard.getByText("73,500 HUF a month · mandate v1")).toBeInTheDocument();
  expect(inCard.getByRole("progressbar", { name: "Emergency fund" })).toHaveAttribute("aria-valuenow", "96");
  expect(inCard.getByText("720,000 of 750,000 HUF")).toBeInTheDocument();
  expect(inCard.getByText("0 of 300,000 HUF · due 2027-08-01")).toBeInTheDocument();
  expect(inCard.getByText("13,500 HUF a month · starts 2026-11-01")).toBeInTheDocument();
  expect(inCard.getByRole("link", { name: "View savings plan" })).toHaveAttribute("href", "/plan");
});

test("shows a start link when there is no active plan", async () => {
  start(null);
  expect(await screen.findByRole("link", { name: "Start a savings plan" })).toHaveAttribute("href", "/questionnaire");
});

test("renders transactions and the rule lines verbatim", async () => {
  start(PLAN);
  expect(await screen.findByText("Rent")).toBeInTheDocument();
  expect(await screen.findByText(RULES.lines[0] ?? "")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd frontend && npx vitest run src/screens/home src/components`
Expected: FAIL — `Failed to resolve import "./HomeScreen"` / `"./TransactionRow"`.

- [ ] **Step 3: Hooks**

Append to `frontend/src/api/hooks.ts` (extend the type import with `AccountOut, AnalysisOut, PlanOut, RulesOut`):

```ts
export function useAccount() {
  return useQuery({ queryKey: keys.account, queryFn: () => apiFetch<AccountOut>("/api/account") });
}

export function useRules() {
  return useQuery({ queryKey: keys.rules, queryFn: () => apiFetch<RulesOut>("/api/rules") });
}

export function useAnalysis() {
  return useQuery({ queryKey: keys.analysis, queryFn: () => apiFetch<AnalysisOut>("/api/analysis") });
}

/** The accepted or paused plan, or null when there is none (404). */
export function useActivePlan() {
  return useQuery({
    queryKey: keys.activePlan,
    queryFn: () => orNull(apiFetch<PlanOut>("/api/plans/active"), 404),
  });
}
```

- [ ] **Step 4: TransactionRow**

`frontend/src/components/TransactionRow.tsx`:

```tsx
import type { TransactionOut } from "../api/types";
import { formatSigned } from "../format";

/** Figma TransactionRow (frame 3:191). */
export function TransactionRow({ transaction }: { transaction: TransactionOut }) {
  const description = transaction.description || "Transaction";
  const meta = transaction.own_transfer
    ? `${transaction.booked_on} · Own transfer, ignored in surplus`
    : transaction.booked_on;
  return (
    <li className="flex min-h-touch items-center gap-3 border-b border-border py-3 last:border-b-0">
      <span aria-hidden="true" className="flex size-8 items-center justify-center rounded-full bg-primary-subtle text-caption text-primary">
        {description.charAt(0)}
      </span>
      <div className="flex-1">
        <p className="text-body font-semibold">{description}</p>
        <p className="text-caption text-text-muted">{meta}</p>
      </div>
      <p className="text-body font-semibold">{formatSigned(transaction.amount)}</p>
    </li>
  );
}
```

- [ ] **Step 5: Home screen**

`frontend/src/screens/home/HomeScreen.tsx`:

```tsx
import { Link } from "react-router";
import { useAccount, useActivePlan, useAnalysis, useMe, useRules } from "../../api/hooks";
import type { PlanItemOut, PlanOut } from "../../api/types";
import { Badge } from "../../components/Badge";
import { buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Icon } from "../../components/Icon";
import { ProgressBar } from "../../components/ProgressBar";
import { TransactionRow } from "../../components/TransactionRow";
import { displayName, formatHuf, formatNumber } from "../../format";

function itemCaption(item: PlanItemOut, plan: PlanOut): string {
  if (item.target_amount === null) {
    return `${formatHuf(item.monthly_amount)} a month · starts ${plan.next_transfer_on}`;
  }
  const saved = `${formatNumber(item.saved_amount)} of ${formatHuf(item.target_amount)}`;
  return item.due_on ? `${saved} · due ${item.due_on}` : saved;
}

function PlanCard({ plan }: { plan: PlanOut | null }) {
  if (plan === null) {
    return (
      <Card title="Your savings plan">
        <p className="text-text-muted">You have no savings plan yet.</p>
        <Link to="/questionnaire" className={`${buttonClass("primary")} mt-4 w-full`}>
          Start a savings plan
        </Link>
      </Card>
    );
  }
  return (
    <section className="rounded-lg border border-border bg-surface p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-h3">Your savings plan</h2>
        <Badge tone={plan.status === "accepted" ? "success" : "warning"}>
          {plan.status === "accepted" ? "Active" : "Paused"}
        </Badge>
      </div>
      <p className="mt-1 text-caption text-text-muted">
        {formatHuf(plan.monthly_amount)} a month · mandate v{plan.mandate_version}
      </p>
      <ul className="mt-4 space-y-4">
        {plan.items.map((item) => (
          <li key={item.position}>
            <div className="flex justify-between text-body font-semibold">
              <span>{item.label}</span>
              {item.progress_percent !== null ? <span className="text-primary">{item.progress_percent}%</span> : null}
            </div>
            {item.progress_percent !== null ? (
              <div className="mt-2">
                <ProgressBar label={item.label} percent={item.progress_percent} />
              </div>
            ) : null}
            <p className="mt-1 text-caption text-text-muted">{itemCaption(item, plan)}</p>
          </li>
        ))}
      </ul>
      <Link to="/plan" className={`${buttonClass("secondary")} mt-4 w-full`}>
        View savings plan
      </Link>
    </section>
  );
}

/** Figma 02 Home (5:118). Every value comes from the API. */
export function HomeScreen() {
  const me = useMe();
  const account = useAccount();
  const plan = useActivePlan();
  const analysis = useAnalysis();
  const rules = useRules();

  const error = account.error ?? plan.error ?? analysis.error ?? rules.error;
  if (error) return <ErrorMessage error={error} />;
  if (!account.data || plan.data === undefined) return <p>Loading…</p>;

  const median = analysis.data?.median_surplus;
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-h1">Hello, {displayName(me.data?.username ?? "")}</h1>
        <p className="text-text-muted">Here is where your money stands today, {account.data.today}.</p>
      </header>
      <div className="grid gap-6 lg:grid-cols-5">
        <section className="flex flex-col justify-between gap-8 rounded-lg bg-primary p-6 text-on-primary lg:col-span-3">
          <div>
            <p className="text-body">Current account balance</p>
            <p className="mt-2">
              <span className="text-number">{formatNumber(account.data.balance)}</span> <span className="text-h3">HUF</span>
            </p>
            <p className="mt-1 text-caption">{account.data.name} · simulated</p>
          </div>
          <dl className="grid grid-cols-3 gap-4 text-caption">
            <div>
              <dt>Median monthly surplus</dt>
              <dd className="text-body font-semibold">{median === null || median === undefined ? "—" : formatHuf(median)}</dd>
            </div>
            <div>
              <dt>Minimum balance kept</dt>
              <dd className="text-body font-semibold">{formatHuf(account.data.min_balance)}</dd>
            </div>
            <div>
              <dt>Next transfer</dt>
              <dd className="text-body font-semibold">{plan.data?.status === "accepted" ? plan.data.next_transfer_on : "—"}</dd>
            </div>
          </dl>
        </section>
        <div className="lg:col-span-2">
          <PlanCard plan={plan.data} />
        </div>
        <Card title="Recent transactions" className="lg:col-span-3">
          <ul>
            {account.data.transactions.map((transaction) => (
              <TransactionRow key={transaction.id} transaction={transaction} />
            ))}
          </ul>
        </Card>
        <Card title="How the plan is calculated" className="lg:col-span-2">
          <ul className="space-y-3">
            {(rules.data?.lines ?? []).map((line) => (
              <li key={line} className="flex gap-2 text-body">
                <Icon name="chevron-right" className="mt-0.5 size-4 text-primary" />
                {line}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
```

In `frontend/src/App.tsx`, import `HomeScreen` and replace the `/` placeholder route element with `<HomeScreen />`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass. The App tests still pass: they mock only `/api/auth/me`, so Home shows an error for the unmocked `/api/account` but the layout's navigation is there. If an App test fails because of that error, add `"GET /api/account"` etc. mocks to those tests rather than weakening an assertion.

- [ ] **Step 7: Lint, docs**

`CHANGELOG.md`, `### Added`: `- Home screen (Figma 02): balance, minimum balance and next transfer, savings plan progress from the API, recent transactions, rule summary from RuleConfig.`

Tick in `docs/tasks.md`: "Shared components: Button, TransactionRow, SideNav (44 px touch targets, accessible labels)."

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): home screen from figma 02`

---

### Task 11: Questionnaire (03): fixed questions, client parsing, submit and propose

Deliverable: Figma 03 (`6:169`): three fixed questions (emergency fund, risk 1–5 radio group, planned expenses with add/remove), keyboard hints, client-side parsing of amounts (no request on invalid input), then `POST /api/questionnaire` + `POST /api/plans`; a plan opens step 2 (`/plans/:id/analysis`). The 09 / 10 outcomes and server field errors are Task 12.

**Files:**
- Create: `frontend/src/screens/questionnaire/{QuestionnaireScreen,RiskOptions,ExpenseRows,answers}.tsx`, `frontend/src/screens/questionnaire/QuestionnaireScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `POST /api/questionnaire` (201 `{id}`), `POST /api/plans` (`ProposalOut`); `keys` (Task 9); `FlowLayout` (Task 8); `TextField`, `Button`, `Card`, `Kbd`, `ErrorMessage` (Task 7); `parseHuf`, `AMOUNT_HINT` (Task 7); `QuestionnaireIn`, `ProposalOut` (Task 6).
- Produces:
  - `useSubmitAnswers()` — mutation `(answers: QuestionnaireIn) => Promise<ProposalOut>` (both requests in order); on success invalidates `keys.plans` and `keys.analysis`.
  - `answers.ts`: `interface ExpenseDraft { name: string; amount: string; dueOn: string }`, `interface Draft { fund: string; risk: number | null; expenses: ExpenseDraft[] }`, `type FieldErrors = Record<string, string>` (keys use the backend field names: `existing_emergency_fund`, `risk_score`, `planned_expenses.N.name|amount|due_on`, `expected_monthly_savings`), `EMPTY_DRAFT`, `toAnswers(draft: Draft, expected: number | null): { answers: QuestionnaireIn } | { errors: FieldErrors }`.
  - `RiskOptions({ value, onChange, error })`, `ExpenseRows({ rows, errors, onChange })`.
  - `QuestionnaireScreen` at `/questionnaire` (FlowLayout step 1 "Your answers", back `/`). Task 12 adds `outcome` views.

- [ ] **Step 1: Write the failing tests**

`frontend/src/screens/questionnaire/QuestionnaireScreen.test.tsx`:

```tsx
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { PLAN } from "../../test/fixtures";
import { mockApi, renderScreen, type Call } from "../../test/render";
import { QuestionnaireScreen } from "./QuestionnaireScreen";

const PROPOSAL = { outcome: "plan", plan: PLAN, explanations: PLAN.explanations };

/** Writes only: the screen also reads /api/rules. */
function posts(calls: Call[]): Call[] {
  return calls.filter((call) => call.method === "POST");
}

function start(routes = {}) {
  const calls = mockApi({
    "GET /api/rules": { body: { lines: ["a", "b", "Money needed within 12 months goes only to low-risk, liquid products.", "d"] } },
    "POST /api/questionnaire": { status: 201, body: { id: 1 } },
    "POST /api/plans": { body: PROPOSAL },
    ...routes,
  });
  renderScreen(<QuestionnaireScreen />, { path: "/questionnaire" });
  return { calls, user: userEvent.setup() };
}

test("submits the answers and opens the spending analysis", async () => {
  const { calls, user } = start();
  await user.type(screen.getByLabelText("Existing emergency fund"), "720,000");
  await user.click(screen.getByRole("radio", { name: "2 Low" }));
  await user.click(screen.getByRole("button", { name: "Add an expense" }));
  await user.type(screen.getByLabelText("What for"), "New laptop");
  await user.type(screen.getByLabelText("Amount"), "300 000");
  await user.type(screen.getByLabelText("Due date"), "2027-08-01");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(await screen.findByText("Navigated to /plans/7/analysis")).toBeInTheDocument();
  expect(posts(calls).map((c) => c.path)).toEqual(["/api/questionnaire", "/api/plans"]);
  expect(posts(calls)[0]?.body).toEqual({
    risk_score: 2,
    existing_emergency_fund: 720_000,
    expected_monthly_savings: null,
    planned_expenses: [{ name: "New laptop", amount: 300_000, due_on: "2027-08-01" }],
  });
});

test("rejects a decimal emergency fund without calling the API", async () => {
  const { calls, user } = start();
  await user.type(screen.getByLabelText("Existing emergency fund"), "100.5");
  await user.click(screen.getByRole("radio", { name: "3 Medium" }));
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(screen.getByLabelText("Existing emergency fund")).toHaveAccessibleDescription(
    "Whole forints. Cannot be negative. Money you can reach at short notice. Enter 0 if you have none.",
  );
  expect(posts(calls)).toEqual([]);
});

test("requires a risk score", async () => {
  const { calls, user } = start();
  await user.type(screen.getByLabelText("Existing emergency fund"), "0");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(await screen.findByText("Choose how much risk you accept.")).toBeInTheDocument();
  expect(posts(calls)).toEqual([]);
});

test("a negative expense amount shows a field error without calling the API", async () => {
  const { calls, user } = start();
  await user.type(screen.getByLabelText("Existing emergency fund"), "0");
  await user.click(screen.getByRole("radio", { name: "3 Medium" }));
  await user.click(screen.getByRole("button", { name: "Add an expense" }));
  await user.type(screen.getByLabelText("What for"), "Holiday");
  await user.type(screen.getByLabelText("Amount"), "-50,000");
  await user.type(screen.getByLabelText("Due date"), "2027-01-01");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(screen.getByLabelText("Amount")).toHaveAttribute("aria-invalid", "true");
  expect(screen.getByText("Enter a positive whole amount in forints.")).toBeInTheDocument();
  expect(posts(calls)).toEqual([]);
});

test("an expense row can be removed", async () => {
  const { user } = start();
  await user.click(screen.getByRole("button", { name: "Add an expense" }));
  await user.click(screen.getByRole("button", { name: "Remove expense 1" }));
  expect(screen.queryByLabelText("What for")).toBeNull();
});
```

Each expense row labels its fields "What for", "Amount" and "Due date"; with more rows, tests use `getAllByLabelText`. The fund field's description order is error, then hint.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd frontend && npx vitest run src/screens/questionnaire`
Expected: FAIL — `Failed to resolve import "./QuestionnaireScreen"`.

- [ ] **Step 3: Draft parsing (pure)**

`frontend/src/screens/questionnaire/answers.ts`:

```ts
import type { QuestionnaireIn } from "../../api/types";
import { AMOUNT_HINT, parseHuf } from "../../format";

export interface ExpenseDraft {
  name: string;
  amount: string;
  dueOn: string;
}

export interface Draft {
  fund: string;
  risk: number | null;
  expenses: ExpenseDraft[];
}

/** Keys are the backend field names, so server errors (ApiError.field) land in the same map. */
export type FieldErrors = Record<string, string>;

export const EMPTY_DRAFT: Draft = { fund: "", risk: null, expenses: [] };

export const POSITIVE_HINT = "Enter a positive whole amount in forints.";

/** Parse the typed answers. Only shape checks: business rules (past dates) are the server's. */
export function toAnswers(draft: Draft, expected: number | null): { answers: QuestionnaireIn } | { errors: FieldErrors } {
  const errors: FieldErrors = {};
  const fund = parseHuf(draft.fund);
  if (fund === null) errors.existing_emergency_fund = AMOUNT_HINT;
  if (draft.risk === null) errors.risk_score = "Choose how much risk you accept.";
  const expenses = draft.expenses.map((row, index) => {
    const amount = parseHuf(row.amount);
    if (row.name.trim() === "") errors[`planned_expenses.${index}.name`] = "Name the expense.";
    if (amount === null || amount === 0) errors[`planned_expenses.${index}.amount`] = POSITIVE_HINT;
    if (row.dueOn === "") errors[`planned_expenses.${index}.due_on`] = "Pick a due date.";
    return { name: row.name.trim(), amount: amount ?? 0, due_on: row.dueOn };
  });
  if (Object.keys(errors).length > 0 || fund === null || draft.risk === null) return { errors };
  return {
    answers: {
      risk_score: draft.risk,
      existing_emergency_fund: fund,
      expected_monthly_savings: expected,
      planned_expenses: expenses,
    },
  };
}
```

- [ ] **Step 4: Hook**

Append to `frontend/src/api/hooks.ts` (extend the type import with `IdOut, ProposalOut, QuestionnaireIn`):

```ts
/** Store the answers, then ask the rule engine for a plan (AC5, AC6 outcomes included). */
export function useSubmitAnswers() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (answers: QuestionnaireIn) => {
      await apiFetch<IdOut>("/api/questionnaire", { method: "POST", body: answers });
      return apiFetch<ProposalOut>("/api/plans", { method: "POST" });
    },
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.analysis });
    },
  });
}
```

- [ ] **Step 5: Components and screen**

`frontend/src/screens/questionnaire/RiskOptions.tsx`:

```tsx
const OPTIONS = [
  [1, "Lowest"],
  [2, "Low"],
  [3, "Medium"],
  [4, "High"],
  [5, "Highest"],
] as const;

/** Figma RiskOption (frame 2:182): native radios, so ← → change the score. */
export function RiskOptions({ value, onChange, error }: { value: number | null; onChange: (risk: number) => void; error?: string }) {
  return (
    <div>
      <div className="grid grid-cols-5 gap-2">
        {OPTIONS.map(([score, name]) => (
          <label
            key={score}
            className={`flex min-h-touch cursor-pointer flex-col items-center justify-center rounded-md border px-2 py-3 has-focus-visible:shadow-focus ${value === score ? "border-primary bg-primary-subtle text-primary" : "border-border hover:bg-surface-hover"}`}
          >
            <input
              type="radio"
              name="risk"
              className="sr-only"
              aria-label={`${score} ${name}`}
              checked={value === score}
              onChange={() => onChange(score)}
            />
            <span className="text-h3">{score}</span>
            <span className="text-caption">{name}</span>
          </label>
        ))}
      </div>
      {error ? <p className="mt-2 text-caption text-danger">{error}</p> : null}
    </div>
  );
}
```

`frontend/src/screens/questionnaire/ExpenseRows.tsx`:

```tsx
import { Button } from "../../components/Button";
import { TextField } from "../../components/TextField";
import type { ExpenseDraft, FieldErrors } from "./answers";

const EMPTY_ROW: ExpenseDraft = { name: "", amount: "", dueOn: "" };
const MAX_ROWS = 10; // QuestionnaireIn.planned_expenses max_length

export function ExpenseRows({ rows, errors, onChange }: { rows: ExpenseDraft[]; errors: FieldErrors; onChange: (rows: ExpenseDraft[]) => void }) {
  function update(index: number, change: Partial<ExpenseDraft>) {
    onChange(rows.map((row, i) => (i === index ? { ...row, ...change } : row)));
  }
  return (
    <div className="space-y-4">
      {rows.map((row, index) => (
        <div key={index} className="grid items-start gap-3 md:grid-cols-4">
          <TextField label="What for" value={row.name} maxLength={100} error={errors[`planned_expenses.${index}.name`]} onChange={(e) => update(index, { name: e.target.value })} />
          <TextField label="Amount" inputMode="numeric" suffix="HUF" value={row.amount} error={errors[`planned_expenses.${index}.amount`]} onChange={(e) => update(index, { amount: e.target.value })} />
          <TextField label="Due date" type="date" value={row.dueOn} error={errors[`planned_expenses.${index}.due_on`]} onChange={(e) => update(index, { dueOn: e.target.value })} />
          <Button variant="ghost" aria-label={`Remove expense ${index + 1}`} className="md:mt-7" onClick={() => onChange(rows.filter((_, i) => i !== index))}>
            Remove
          </Button>
        </div>
      ))}
      {rows.length < MAX_ROWS ? (
        <Button variant="ghost" onClick={() => onChange([...rows, EMPTY_ROW])}>
          {rows.length === 0 ? "Add an expense" : "Add another expense"}
        </Button>
      ) : null}
    </div>
  );
}
```

The test names the add button "Add an expense" for the first row; after that it reads "Add another expense" (Figma 03). `index + 1` is a row number for the label, not money.

`frontend/src/screens/questionnaire/QuestionnaireScreen.tsx`:

```tsx
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useRules, useSubmitAnswers } from "../../api/hooks";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { Kbd } from "../../components/Kbd";
import { TextField } from "../../components/TextField";
import { EMPTY_DRAFT, toAnswers, type Draft, type FieldErrors } from "./answers";
import { ExpenseRows } from "./ExpenseRows";
import { RiskOptions } from "./RiskOptions";

/** Figma 03 Questionnaire (6:169), step 1 of 4. */
export function QuestionnaireScreen() {
  const navigate = useNavigate();
  const submit = useSubmitAnswers();
  const rules = useRules();
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);
  const [errors, setErrors] = useState<FieldErrors>({});

  function send(expected: number | null) {
    const parsed = toAnswers(draft, expected);
    if ("errors" in parsed) {
      setErrors(parsed.errors);
      return;
    }
    setErrors({});
    submit.mutate(parsed.answers, {
      onSuccess: (proposal) => {
        if (proposal.outcome === "plan" && proposal.plan) navigate(`/plans/${proposal.plan.id}/analysis`);
        // Task 12: no_surplus (09) and needs_expected_savings (10) views.
      },
    });
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    send(null);
  }

  return (
    <FlowLayout step={1} title="Your answers" backTo="/">
      <form className="space-y-6" onSubmit={onSubmit} noValidate>
        <header>
          <h1 className="text-h1">Tell us about your situation</h1>
          <p className="text-text-muted">
            Three fixed questions. Your answers set the emergency-fund gap, the risk limit and the planned expenses in
            your plan.
          </p>
          <p className="mt-3 flex flex-wrap items-center gap-2 text-caption text-text-muted">
            <Kbd>Tab</Kbd> moves between fields <Kbd>←</Kbd> <Kbd>→</Kbd> change the risk score <Kbd>Enter ↵</Kbd>{" "}
            continues
          </p>
        </header>
        <Card title="1. How much do you already have in an emergency fund?">
          <TextField
            label="Existing emergency fund"
            inputMode="numeric"
            suffix="HUF"
            value={draft.fund}
            error={errors.existing_emergency_fund}
            hint="Money you can reach at short notice. Enter 0 if you have none."
            onChange={(e) => setDraft({ ...draft, fund: e.target.value })}
          />
        </Card>
        <Card title="2. How much risk are you comfortable with?">
          <fieldset>
            <legend className="mb-3 text-body text-text-muted">
              1 = I never want to see a loss · 5 = I accept large swings for a higher long-term return. Products above
              your score never appear in the plan.
            </legend>
            <RiskOptions value={draft.risk} error={errors.risk_score} onChange={(risk) => setDraft({ ...draft, risk })} />
          </fieldset>
        </Card>
        <Card title="3. Any large expenses planned?">
          {/* lines[2] is the liquid-horizon rule, filled from RuleConfig (not hard-coded "12 months"). */}
          <p className="mb-4 text-body text-text-muted">{rules.data?.lines[2]}</p>
          <ExpenseRows rows={draft.expenses} errors={errors} onChange={(expenses) => setDraft({ ...draft, expenses })} />
        </Card>
        <ErrorMessage error={submit.error} />
        <div className="flex items-center justify-end gap-3">
          <span className="text-caption text-text-muted">
            or press <Kbd>Enter ↵</Kbd>
          </span>
          <Button type="submit" disabled={submit.isPending}>
            Continue
          </Button>
        </div>
      </form>
    </FlowLayout>
  );
}
```

The fund hint ("Enter 0 if you have none") is fixed Figma copy, not a rule result.

In `frontend/src/App.tsx`, inside `<Route element={<RequireLogin />}>` and outside the layout route, add `<Route path="/questionnaire" element={<QuestionnaireScreen />} />`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/screens/questionnaire`
Expected: 5 passed.

- [ ] **Step 7: Lint, changelog**

`CHANGELOG.md`, `### Added`: `- Questionnaire (Figma 03): fixed questions, risk radio group, planned expenses, amounts parsed as whole forints before any request (AC8).`

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): questionnaire screen from figma 03`

---

### Task 12: No surplus (09), too little data (10) and server field errors (AC5, AC6, AC8)

Deliverable: after submit, the `no_surplus` outcome shows Figma 09 (`10:791`) and `needs_expected_savings` shows Figma 10 (`10:852`) inside `/questionnaire`, with the backend explanation verbatim. On 10 the customer enters the expected monthly savings and the same answers are sent again. A 422 with `field` is shown under that field.

**Files:**
- Create: `frontend/src/screens/questionnaire/{NoSurplusView,TooLittleDataView}.tsx`, `frontend/src/screens/questionnaire/outcomes.test.tsx`
- Modify: `frontend/src/screens/questionnaire/QuestionnaireScreen.tsx`, `docs/traceability.md`, `CHANGELOG.md`, `docs/tasks.md`

**Interfaces:**
- Consumes: `useSubmitAnswers`, `useAnalysis` (Tasks 10, 11), `ApiError.field` (Task 6), `FlowLayout`, `Card`, `StatTile`, `TextField`, `Button`, `buttonClass`, `Icon`, `Kbd`, `ErrorMessage`, `parseHuf`, `formatHuf`, `POSITIVE_HINT`, `toAnswers` (Task 11), `ProposalOut`.
- Produces: `NoSurplusView({ explanations: string[] })` (reads `useAnalysis()` for the median and months), `TooLittleDataView({ explanations, pending, error, onSubmit(expected: number) })`; `QuestionnaireScreen` keeps `outcome: ProposalOut | null` and the draft.

- [ ] **Step 1: Write the failing tests**

`frontend/src/screens/questionnaire/outcomes.test.tsx`:

```tsx
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { ANALYSIS, plan } from "../../test/fixtures";
import { mockApi, renderScreen, type Handler } from "../../test/render";
import { QuestionnaireScreen } from "./QuestionnaireScreen";

const RULES = { body: { lines: ["a", "b", "c", "d"] } };
const NO_SURPLUS =
  "Your median monthly surplus over the last 6 months is -40,000 HUF, so there is no surplus to save. No investment plan was created.";
const TOO_LITTLE =
  "We found only 2 full months of transactions; at least 3 are needed for an estimate. Please enter how much you expect to save each month.";

async function answer(routes: Record<string, Handler>) {
  const calls = mockApi({ "GET /api/rules": RULES, "POST /api/questionnaire": { status: 201, body: { id: 1 } }, ...routes });
  renderScreen(<QuestionnaireScreen />, { path: "/questionnaire" });
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Existing emergency fund"), "0");
  await user.click(screen.getByRole("radio", { name: "3 Medium" }));
  await user.click(screen.getByRole("button", { name: "Continue" }));
  return { calls, user };
}

test("test_ac5_no_surplus_shows_explanation_without_plan", async () => {
  await answer({
    "POST /api/plans": { body: { outcome: "no_surplus", plan: null, explanations: [NO_SURPLUS] } },
    "GET /api/analysis": { body: { ...ANALYSIS, median_surplus: -40_000, monthly_amount: 0, explanations: [NO_SURPLUS] } },
  });
  expect(await screen.findByRole("heading", { name: "No surplus to save right now" })).toBeInTheDocument();
  expect(screen.getByText(NO_SURPLUS)).toBeInTheDocument();
  expect(await screen.findByText("-40,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("None")).toBeInTheDocument(); // orders created
  expect(screen.getByRole("link", { name: "Back to home" })).toHaveAttribute("href", "/");
  expect(screen.queryByRole("button", { name: "Continue to mandate" })).toBeNull();
});

test("test_ac6_too_little_data_asks_for_expected_savings", async () => {
  let proposals = 0;
  const { calls, user } = await answer({
    "POST /api/plans": () => {
      proposals += 1;
      return proposals === 1
        ? { body: { outcome: "needs_expected_savings", plan: null, explanations: [TOO_LITTLE] } }
        : { body: { outcome: "plan", plan: plan({ id: 9, confidence: "none" }), explanations: [] } };
    },
  });
  expect(await screen.findByRole("heading", { name: "We need a little more data" })).toBeInTheDocument();
  expect(screen.getByText(TOO_LITTLE)).toBeInTheDocument();
  await user.type(screen.getByLabelText("Expected monthly savings"), "40000");
  await user.click(screen.getByRole("button", { name: "Show my plan" }));
  expect(await screen.findByText("Navigated to /plans/9")).toBeInTheDocument();
  const answers = calls.filter((c) => c.path === "/api/questionnaire").map((c) => c.body);
  expect(answers).toEqual([
    { risk_score: 3, existing_emergency_fund: 0, expected_monthly_savings: null, planned_expenses: [] },
    { risk_score: 3, existing_emergency_fund: 0, expected_monthly_savings: 40_000, planned_expenses: [] },
  ]);
});

test("too little data rejects an empty expected amount without calling the API", async () => {
  const { calls, user } = await answer({
    "POST /api/plans": { body: { outcome: "needs_expected_savings", plan: null, explanations: [TOO_LITTLE] } },
  });
  await screen.findByRole("heading", { name: "We need a little more data" });
  const before = calls.length;
  await user.click(screen.getByRole("button", { name: "Show my plan" }));
  expect(screen.getByLabelText("Expected monthly savings")).toHaveAttribute("aria-invalid", "true");
  expect(calls.length).toBe(before);
});

test("test_ac8_past_expense_date_shows_the_server_message_at_the_field", async () => {
  mockApi({
    "GET /api/rules": RULES,
    "POST /api/questionnaire": {
      status: 422,
      body: { detail: "The due date of 'Holiday' (2026-09-01) is in the past.", field: "planned_expenses.0.due_on" },
    },
  });
  renderScreen(<QuestionnaireScreen />, { path: "/questionnaire" });
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Existing emergency fund"), "0");
  await user.click(screen.getByRole("radio", { name: "3 Medium" }));
  await user.click(screen.getByRole("button", { name: "Add an expense" }));
  await user.type(screen.getByLabelText("What for"), "Holiday");
  await user.type(screen.getByLabelText("Amount"), "50000");
  await user.type(screen.getByLabelText("Due date"), "2026-09-01");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  expect(await screen.findByText("The due date of 'Holiday' (2026-09-01) is in the past.")).toBeInTheDocument();
  expect(screen.getByLabelText("Due date")).toHaveAttribute("aria-invalid", "true");
  expect(screen.queryByRole("alert")).toBeNull(); // shown at the field, not as a form error
});
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd frontend && npx vitest run src/screens/questionnaire/outcomes.test.tsx`
Expected: FAIL — no "No surplus to save right now" heading.

- [ ] **Step 3: The two views**

`frontend/src/screens/questionnaire/NoSurplusView.tsx`:

```tsx
import { Link } from "react-router";
import { useAnalysis } from "../../api/hooks";
import { buttonClass } from "../../components/Button";
import { Icon } from "../../components/Icon";
import { StatTile } from "../../components/StatTile";
import { formatHuf } from "../../format";

/** Figma 09 No surplus (10:791), AC5: an explanation instead of an investment. */
export function NoSurplusView({ explanations }: { explanations: string[] }) {
  const analysis = useAnalysis();
  const median = analysis.data?.median_surplus;
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-border bg-surface p-8 text-center">
        <span className="mx-auto flex size-12 items-center justify-center rounded-full bg-info-bg text-info">
          <Icon name="info" />
        </span>
        <h1 className="mt-4 text-h1">No surplus to save right now</h1>
        {explanations.map((text) => (
          <p key={text} role="status" className="mt-2 text-text-muted">
            {text}
          </p>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <StatTile label="Median monthly surplus" value={median === null || median === undefined ? "—" : formatHuf(median)} />
        <StatTile label="Months analysed" value={String(analysis.data?.months_of_data ?? "—")} />
        <StatTile label="Orders created" value="None" />
      </div>
      <Link to="/" className={buttonClass("primary")}>
        Back to home
      </Link>
    </div>
  );
}
```

`frontend/src/screens/questionnaire/TooLittleDataView.tsx`:

```tsx
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
    <form className="space-y-6 rounded-lg border border-border bg-surface p-8" onSubmit={submit} noValidate>
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
```

- [ ] **Step 4: Wire outcomes and server field errors into the screen**

In `QuestionnaireScreen.tsx`:

1. Add imports: `import { ApiError } from "../../api/client";`, `import type { ProposalOut } from "../../api/types";`, `import { NoSurplusView } from "./NoSurplusView";`, `import { TooLittleDataView } from "./TooLittleDataView";`.
2. Add state: `const [outcome, setOutcome] = useState<ProposalOut | null>(null);`.
3. Replace `send` with:

```tsx
  function send(expected: number | null) {
    const parsed = toAnswers(draft, expected);
    if ("errors" in parsed) {
      setErrors(parsed.errors);
      return;
    }
    setErrors({});
    submit.mutate(parsed.answers, {
      onSuccess: (proposal) => {
        if (proposal.outcome === "plan" && proposal.plan) {
          // With an expected amount there is no history to analyse: go straight to the plan.
          navigate(expected === null ? `/plans/${proposal.plan.id}/analysis` : `/plans/${proposal.plan.id}`);
          return;
        }
        setOutcome(proposal);
      },
      onError: (error) => {
        if (error instanceof ApiError && error.field) setErrors({ [error.field]: error.message });
      },
    });
  }

  // A field error is shown at the field, so the form-level alert shows only the others.
  const formError = submit.error instanceof ApiError && submit.error.field ? null : submit.error;
```

4. Change `<ErrorMessage error={submit.error} />` to `<ErrorMessage error={formError} />`.
5. Before the main `return`, add:

```tsx
  // 09 and 10 live on /questionnaire, so a Back link would point to the same URL: the
  // "Change my answers" button returns to the form with the draft kept.
  if (outcome?.outcome === "no_surplus") {
    return (
      <FlowLayout step={2} title="Spending analysis" backTo={null}>
        <NoSurplusView explanations={outcome.explanations} />
        <Button variant="secondary" className="mt-4" onClick={() => setOutcome(null)}>
          Change my answers
        </Button>
      </FlowLayout>
    );
  }
  if (outcome?.outcome === "needs_expected_savings") {
    return (
      <FlowLayout step={2} title="Spending analysis" backTo={null}>
        <TooLittleDataView
          explanations={outcome.explanations}
          pending={submit.isPending}
          error={formError}
          fieldError={errors.expected_monthly_savings}
          onSubmit={(expected) => send(expected)}
        />
        <Button variant="secondary" className="mt-4" onClick={() => setOutcome(null)}>
          Change my answers
        </Button>
      </FlowLayout>
    );
  }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/screens/questionnaire`
Expected: all pass (5 + 4).

- [ ] **Step 6: Docs**

`docs/traceability.md`: AC5 evidence append `; frontend/src/screens/questionnaire/outcomes.test.tsx::test_ac5_no_surplus_shows_explanation_without_plan`; AC6 append `; frontend/src/screens/questionnaire/outcomes.test.tsx::test_ac6_too_little_data_asks_for_expected_savings`; AC8 append `; frontend/src/screens/questionnaire/outcomes.test.tsx::test_ac8_past_expense_date_shows_the_server_message_at_the_field`.

`CHANGELOG.md`, `### Added`: `- No-surplus (Figma 09) and too-little-data (Figma 10) states with the backend explanation; server validation errors shown at the field (AC5, AC6, AC8).`

Tick in `docs/tasks.md`: "Empty/explanation states: no surplus (AC5), too little data asks for expected monthly savings (AC6)." and "AC5 edge: negative median → no plan + message." if still open.

Run: `cd frontend && npm run fmt && npm run lint && cd .. && make docs-check`. Expected: clean, `docs-check: OK`.

- [ ] **Step 7: Suggested commit (user commits)**

`feat(frontend): no-surplus and too-little-data states (AC5, AC6, AC8)`

---

### Task 13: Spending analysis (04), step 2

Deliverable: Figma 04 (`6:305`) at `/plans/:planId/analysis`: three stat tiles, the monthly-surplus bar chart with the median line (tooltip on hover and keyboard focus, no value labels on bars), the backend's median working text, an accessible month table, and "See my plan".

**Files:**
- Create: `frontend/src/screens/analysis/{AnalysisScreen,SurplusChart}.tsx`, `frontend/src/screens/analysis/AnalysisScreen.test.tsx`
- Modify: `frontend/src/format.ts`, `frontend/src/format.test.ts`, `frontend/src/test/setup.ts`, `frontend/src/App.tsx`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `useAnalysis` (Task 10), `FlowLayout`, `StatTile`, `Card`, `buttonClass`, `ErrorMessage`, `formatHuf`, `formatNumber`, `formatMonth` (Tasks 7–8), `AnalysisOut`, fixture `ANALYSIS` (Task 6), Recharts.
- Produces: `formatCompact(amount): string` (`100000` → `"100k"`), `SurplusChart({ months: MonthOut[], median: number | null })`, `AnalysisScreen` at `/plans/:planId/analysis`; `ResizeObserver` stub in `src/test/setup.ts` (Recharts' `ResponsiveContainer` needs it; jsdom lacks it).

- [ ] **Step 1: Write the failing tests**

Append to `frontend/src/format.test.ts` (add `formatCompact` to the import):

```ts
test("formatCompact labels chart axes", () => {
  expect(formatCompact(100_000)).toBe("100k");
  expect(formatCompact(750_000)).toBe("750k");
  expect(formatCompact(0)).toBe("0");
});
```

`frontend/src/screens/analysis/AnalysisScreen.test.tsx`:

```tsx
import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import { ANALYSIS } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { AnalysisScreen } from "./AnalysisScreen";

function start() {
  mockApi({ "GET /api/analysis": { body: ANALYSIS } });
  renderScreen(<AnalysisScreen />, { path: "/plans/:planId/analysis", url: "/plans/7/analysis" });
}

test("test_ac1_analysis_shows_median_and_suggested_amount", async () => {
  start();
  expect(await screen.findByRole("heading", { name: "Your spending analysis" })).toBeInTheDocument();
  expect(screen.getByText("105,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("73,500 HUF")).toBeInTheDocument();
  expect(screen.getByText("70% of the median")).toBeInTheDocument();
  expect(screen.getByText(ANALYSIS.median_explanation ?? "")).toBeInTheDocument();
});

test("lists every month in an accessible table", async () => {
  start();
  const table = await screen.findByRole("table", { name: "Monthly surplus, last 6 months" });
  const rows = within(table).getAllByRole("row");
  expect(rows).toHaveLength(7); // header + 6 months
  expect(within(rows[6] ?? table).getByText("2026-09")).toBeInTheDocument();
  expect(within(rows[6] ?? table).getByText("300,000 HUF")).toBeInTheDocument();
});

test("continues to the plan", async () => {
  start();
  expect(await screen.findByRole("link", { name: "See my plan" })).toHaveAttribute("href", "/plans/7");
  expect(screen.getByText("Step 2 of 4")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd frontend && npx vitest run src/screens/analysis src/format.test.ts`
Expected: FAIL — `formatCompact` missing, `./AnalysisScreen` unresolved.

- [ ] **Step 3: Formatting and the ResizeObserver stub**

Append to `frontend/src/format.ts`:

```ts
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 0 });

/** Chart axis ticks: 100000 → "100k" (Figma 04, 06). */
export function formatCompact(amount: Huf): string {
  return compact.format(amount).toLowerCase();
}
```

Append to `frontend/src/test/setup.ts`:

```ts
// Recharts' ResponsiveContainer needs ResizeObserver, which jsdom lacks. Charts render at zero
// size in tests, so assertions use the month tables, not the SVG.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
globalThis.ResizeObserver = ResizeObserverStub;
```

- [ ] **Step 4: Chart and screen**

`frontend/src/screens/analysis/SurplusChart.tsx`:

```tsx
import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MonthOut } from "../../api/types";
import { formatCompact, formatHuf, formatMonth, formatNumber } from "../../format";

interface Row {
  month: string;
  surplus: number;
}

function SurplusTooltip({ active, payload }: { active?: boolean; payload?: ReadonlyArray<{ payload: Row }> }) {
  const row = payload?.[0]?.payload;
  if (!active || row === undefined) return null;
  return (
    <div className="rounded-md bg-tooltip-bg px-3 py-2 text-caption text-on-primary">
      {row.month} · {formatHuf(row.surplus)}
    </div>
  );
}

/** Figma 04 chart: bars per month, dashed median line labelled in the gutter, values in a
 * tooltip on hover or keyboard focus (Recharts accessibilityLayer). Decorative for screen
 * readers: the table on the screen carries the same values. */
export function SurplusChart({ months, median }: { months: MonthOut[]; median: number | null }) {
  const rows: Row[] = months.map((m) => ({ month: formatMonth(m.month), surplus: m.surplus }));
  return (
    <div aria-hidden="true" className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} accessibilityLayer margin={{ top: 16, right: 72, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--color-chart-grid)" />
          <XAxis dataKey="month" tickLine={false} axisLine={false} />
          <YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} width={48} />
          <Tooltip content={SurplusTooltip} cursor={{ fill: "var(--color-surface-hover)" }} />
          {median === null ? null : (
            <ReferenceLine
              y={median}
              stroke="var(--color-primary)"
              strokeDasharray="4 4"
              label={{ value: `Median ${formatNumber(median)}`, position: "right", fill: "var(--color-primary)", fontSize: 12 }}
            />
          )}
          <Bar dataKey="surplus" fill="var(--color-chart-saved)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

If `tsc` rejects `content={SurplusTooltip}` with the installed Recharts 3 types, type the props as `TooltipContentProps<number, string>` from `recharts` and read `props.payload?.[0]?.payload as Row`; keep the rendered text the same.

`frontend/src/screens/analysis/AnalysisScreen.tsx`:

```tsx
import { Link, useParams } from "react-router";
import { useAnalysis } from "../../api/hooks";
import type { Confidence } from "../../api/types";
import { buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { StatTile } from "../../components/StatTile";
import { formatHuf, formatMonth } from "../../format";
import { SurplusChart } from "./SurplusChart";

const CONFIDENCE_CAPTION: Record<Confidence, string> = {
  normal: "Enough for a full-confidence plan",
  low: "Low confidence: every transfer needs your approval",
  none: "Too few months for an estimate",
};

/** Figma 04 Spending analysis (6:305), step 2 of 4. */
export function AnalysisScreen() {
  const planId = Number(useParams().planId);
  const analysis = useAnalysis();
  const data = analysis.data;
  const title = `Monthly surplus, last ${data?.months.length ?? ""} months`;

  return (
    <FlowLayout step={2} title="Spending analysis" backTo="/questionnaire" wide>
      <div className="space-y-6">
        <header>
          <h1 className="text-h1">Your spending analysis</h1>
          <p className="text-text-muted">
            Surplus = income − expenses per calendar month. Transfers between your own accounts are ignored. The median
            limits the effect of one-off months.
          </p>
        </header>
        <ErrorMessage error={analysis.error} />
        {data ? (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <StatTile
                label="Median monthly surplus"
                value={data.median_surplus === null ? "—" : formatHuf(data.median_surplus)}
                caption={`Last ${data.months.length} complete months`}
              />
              <StatTile
                label="Suggested monthly amount"
                value={data.monthly_amount === null ? "—" : formatHuf(data.monthly_amount)}
                caption={`${data.share_percent}% of the median`}
              />
              <StatTile label="Months analysed" value={String(data.months_of_data)} caption={CONFIDENCE_CAPTION[data.confidence]} />
            </div>
            <Card title={title}>
              <SurplusChart months={data.months} median={data.median_surplus} />
              {data.median_explanation ? <p className="mt-4 text-body text-text-muted">{data.median_explanation}</p> : null}
              <details className="mt-4">
                <summary className="flex min-h-touch cursor-pointer items-center text-body font-semibold text-primary">
                  See month by month
                </summary>
                <table className="mt-2 w-full text-left text-body">
                  <caption className="sr-only">{title}</caption>
                  <thead>
                    <tr className="text-caption text-text-muted">
                      <th className="py-2">Month</th>
                      <th>Income</th>
                      <th>Expenses</th>
                      <th>Surplus</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.months.map((m) => (
                      <tr key={m.month} className="border-t border-border">
                        <td className="py-2">{formatMonth(m.month)}</td>
                        <td>{formatHuf(m.income)}</td>
                        <td>{formatHuf(m.expenses)}</td>
                        <td className="font-semibold">{formatHuf(m.surplus)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            </Card>
            <div className="flex justify-end">
              <Link to={`/plans/${planId}`} className={buttonClass("primary")}>
                See my plan
              </Link>
            </div>
          </>
        ) : null}
      </div>
    </FlowLayout>
  );
}
```

The month count in the captions is `months.length` of the API list (how many rows were analysed), not arithmetic. The `<details>` content is in the DOM while closed, so the table test finds it.

In `frontend/src/App.tsx`, add the flow route `<Route path="/plans/:planId/analysis" element={<AnalysisScreen />} />`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass. `getByText("105,000 HUF")` could also match the median label if Recharts rendered it; the chart is zero-size in jsdom, so it does not. If it does in your Recharts version, scope the query to the stat tiles with `within(screen.getByText("Median monthly surplus").closest("div") ...)`.

- [ ] **Step 6: Docs**

`docs/traceability.md`, AC1 evidence append `; frontend/src/screens/analysis/AnalysisScreen.test.tsx::test_ac1_analysis_shows_median_and_suggested_amount`.

`CHANGELOG.md`, `### Added`: `- Spending analysis (Figma 04): median, suggested amount and months analysed, surplus chart with the median line, the median working and a month table (AC1).`

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 7: Suggested commit (user commits)**

`feat(frontend): spending analysis screen from figma 04 (AC1)`

---

### Task 14: Plan review (05, 05b), step 3: items, time machine summary, edit and reject

Deliverable: Figma 05 (`7:282`), 05b (`10:709`) and 375 px (`10:981`) at `/plans/:planId`: "Why this amount" with the backend explanation and plan facts, priority-ordered items, a time machine summary card with a mini chart, "Want to save less?" (PATCH), "Reject plan", and the sticky summary panel with confidence badge and "Continue to mandate". Low confidence shows the approval notice.

**Files:**
- Create: `frontend/src/components/PlanItemCard.tsx`, `frontend/src/components/SavedChart.tsx`
- Create: `frontend/src/screens/plan-review/PlanReviewScreen.tsx`, `frontend/src/screens/plan-review/machineSummary.ts`, `frontend/src/screens/plan-review/PlanReviewScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `docs/traceability.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `GET /api/plans/{id}`, `PATCH /api/plans/{id}` (`{monthly_amount}`; 409 / 422), `POST /api/plans/{id}/reject`, `GET /api/plans/{id}/time-machine`; `keys` (Task 9); `FlowLayout`, `SummaryPanel` (Task 8); `Card`, `Badge`, `confidenceBadge`, `TextField`, `Button`, `buttonClass`, `Icon`, `ErrorMessage`, `formatHuf`, `formatMonth`, `parseHuf` (Task 7); fixtures `PLAN`, `plan()`, `LOW_CONFIDENCE_PLAN`, `MACHINE`.
- Produces:
  - Hooks: `usePlan(planId)`, `useTimeMachine(planId)`, `useEditPlan(planId)` (mutate `number`), `usePlanAction(action: "reject" | "pause")` (mutate `planId`).
  - `PlanItemCard({ item: PlanItemOut, number: number })` — `<li>`; `SavedChart({ months: BacktestMonthOut[], compact?: boolean })`.
  - `machineSummary(machine: TimeMachineOut): string` (`"147,000 HUF saved · 1 month skipped"`) in `machineSummary.ts` (shared with Task 16).
  - `PlanReviewScreen` at `/plans/:planId` (FlowLayout step 3 "Plan review", back `/plans/:planId/analysis`).

- [ ] **Step 1: Write the failing tests**

`frontend/src/screens/plan-review/PlanReviewScreen.test.tsx`:

```tsx
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { PlanOut } from "../../api/types";
import { LOW_CONFIDENCE_PLAN, MACHINE, PLAN, plan } from "../../test/fixtures";
import { mockApi, renderScreen, type Handler } from "../../test/render";
import { PlanReviewScreen } from "./PlanReviewScreen";

function start(current: PlanOut = PLAN, routes: Record<string, Handler> = {}) {
  const calls = mockApi({
    [`GET /api/plans/${current.id}`]: { body: current },
    [`GET /api/plans/${current.id}/time-machine`]: { body: MACHINE },
    ...routes,
  });
  renderScreen(<PlanReviewScreen />, { path: "/plans/:planId", url: `/plans/${current.id}` });
  return { calls, user: userEvent.setup() };
}

test("test_ac1_plan_review_shows_73500_with_high_confidence", async () => {
  start();
  const panel = await screen.findByRole("complementary", { name: "Summary" });
  expect(within(panel).getByText("73,500 HUF")).toBeInTheDocument();
  expect(within(panel).getByText("High confidence")).toBeInTheDocument();
  expect(screen.getByText(PLAN.explanations[0] ?? "")).toBeInTheDocument();
  expect(within(panel).getByRole("link", { name: "Continue to mandate" })).toHaveAttribute("href", "/plans/7/mandate");
});

test("test_ac2_emergency_fund_is_the_first_item", async () => {
  start();
  const list = await screen.findByRole("list", { name: "Plan items" });
  const [first] = within(list).getAllByRole("listitem");
  expect(first).toHaveTextContent("Emergency fund");
  expect(first).toHaveTextContent("30,000 HUF / month");
});

test("test_ac6_low_confidence_plan_says_every_transfer_needs_approval", async () => {
  start(LOW_CONFIDENCE_PLAN);
  expect(await screen.findByRole("heading", { name: "Every transfer needs your approval" })).toBeInTheDocument();
  expect(screen.getByText(LOW_CONFIDENCE_PLAN.explanations[1] ?? "")).toBeInTheDocument();
  expect(within(screen.getByRole("complementary", { name: "Summary" })).getByText("Low confidence")).toBeInTheDocument();
});

test("shows the time machine summary and links to the month-by-month view", async () => {
  start();
  expect(await screen.findAllByText("147,000 HUF saved · 1 month skipped")).toHaveLength(2); // card + panel
  expect(screen.getByRole("link", { name: "See month by month" })).toHaveAttribute("href", "/plans/7/time-machine");
});

test("rejects a decimal amount without calling the API", async () => {
  const { calls, user } = start();
  const field = await screen.findByLabelText("Monthly amount");
  await user.clear(field);
  await user.type(field, "100.5");
  await user.click(screen.getByRole("button", { name: "Update plan" }));
  expect(field).toHaveAttribute("aria-invalid", "true");
  expect(calls.filter((c) => c.method === "PATCH")).toEqual([]);
});

test("updating the amount sends a whole number and shows the revised plan", async () => {
  const { calls, user } = start(PLAN, {
    "PATCH /api/plans/7": { body: plan({ monthly_amount: 50_000 }) },
  });
  const field = await screen.findByLabelText("Monthly amount");
  await user.clear(field);
  await user.type(field, "50 000");
  await user.click(screen.getByRole("button", { name: "Update plan" }));
  expect(calls.find((c) => c.method === "PATCH")?.body).toEqual({ monthly_amount: 50_000 });
  expect(await within(screen.getByRole("complementary", { name: "Summary" })).findByText("50,000 HUF")).toBeInTheDocument();
});

test("test_ac8_amount_above_proposal_shows_the_server_message", async () => {
  const { user } = start(PLAN, {
    "PATCH /api/plans/7": {
      status: 422,
      body: { detail: "The monthly amount must be between 1 and 73500 HUF.", field: "monthly_amount" },
    },
  });
  const field = await screen.findByLabelText("Monthly amount");
  await user.clear(field);
  await user.type(field, "80000");
  await user.click(screen.getByRole("button", { name: "Update plan" }));
  expect(await screen.findByText("The monthly amount must be between 1 and 73500 HUF.")).toBeInTheDocument();
});

test("test_ac7_rejecting_goes_home_without_orders", async () => {
  const { calls, user } = start(PLAN, { "POST /api/plans/7/reject": { body: plan({ status: "rejected" }) } });
  await user.click(await screen.findByRole("button", { name: "Reject plan" }));
  expect(await screen.findByText("Navigated to /")).toBeInTheDocument();
  expect(calls.some((c) => c.path.endsWith("/accept"))).toBe(false);
});

test("an accepted plan offers no edit or signing", async () => {
  start(plan({ status: "accepted", mandate_version: 1 }));
  expect(await screen.findByRole("link", { name: "Go to your savings plan" })).toHaveAttribute("href", "/plan");
  expect(screen.queryByRole("button", { name: "Update plan" })).toBeNull();
  expect(screen.queryByRole("link", { name: "Continue to mandate" })).toBeNull();
});
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd frontend && npx vitest run src/screens/plan-review`
Expected: FAIL — `./PlanReviewScreen` unresolved.

- [ ] **Step 3: Hooks**

Append to `frontend/src/api/hooks.ts` (types `TimeMachineOut` added to the import):

```ts
export function usePlan(planId: number) {
  return useQuery({ queryKey: keys.plan(planId), queryFn: () => apiFetch<PlanOut>(`/api/plans/${planId}`) });
}

export function useTimeMachine(planId: number) {
  return useQuery({
    queryKey: keys.timeMachine(planId),
    queryFn: () => apiFetch<TimeMachineOut>(`/api/plans/${planId}/time-machine`),
  });
}

/** Lower the amount of a proposed plan (nothing runs until it is accepted). */
export function useEditPlan(planId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (monthlyAmount: number) =>
      apiFetch<PlanOut>(`/api/plans/${planId}`, { method: "PATCH", body: { monthly_amount: monthlyAmount } }),
    onSuccess: async (updated) => {
      client.setQueryData(keys.plan(planId), updated);
      await client.invalidateQueries({ queryKey: keys.timeMachine(planId) });
      await client.invalidateQueries({ queryKey: keys.mandate(planId) });
    },
  });
}

/** Reject a proposed plan or pause an active one; refreshes every plan query and the log. */
export function usePlanAction(action: "reject" | "pause") {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (planId: number) => apiFetch<PlanOut>(`/api/plans/${planId}/${action}`, { method: "POST" }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.activity });
    },
  });
}
```

- [ ] **Step 4: PlanItemCard and SavedChart**

`frontend/src/components/PlanItemCard.tsx`:

```tsx
import type { PlanItemOut } from "../api/types";
import { formatHuf } from "../format";

function details(item: PlanItemOut): string {
  const product = `${item.product.name} · risk ${item.product.risk_level}${item.product.liquid ? " · liquid" : ""}`;
  if (item.kind === "emergency_fund" && item.target_amount !== null) {
    return `${product} · target ${formatHuf(item.target_amount)}, ${formatHuf(item.saved_amount)} already saved`;
  }
  if (item.kind === "planned_expense" && item.target_amount !== null) {
    return `${product} · ${formatHuf(item.target_amount)} needed by ${item.due_on ?? "the due date"}`;
  }
  return `${product} · the rest of the monthly amount`;
}

/** Figma PlanItem (frame 3:191): priority number, label, product line, monthly amount. */
export function PlanItemCard({ item, number }: { item: PlanItemOut; number: number }) {
  return (
    <li className="flex items-center gap-4 rounded-md border border-border p-4">
      <span aria-hidden="true" className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary text-caption text-on-primary">
        {number}
      </span>
      <div className="flex-1">
        <p className="text-h3">
          {item.label}
          {item.due_on ? ` · due ${item.due_on}` : ""}
        </p>
        <p className="text-caption text-text-muted">{details(item)}</p>
      </div>
      <p className="text-body font-semibold whitespace-nowrap">{formatHuf(item.monthly_amount)} / month</p>
    </li>
  );
}
```

`number` is the 1-based display position (`item.position + 1` at the call site; a list index, not money).

`frontend/src/components/SavedChart.tsx`:

```tsx
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { BacktestMonthOut } from "../api/types";
import { formatCompact, formatHuf, formatMonth, monthName } from "../format";

interface Row {
  month: string;
  label: string;
  saved: number;
  skipped: boolean;
}

function SavedTooltip({ active, payload }: { active?: boolean; payload?: ReadonlyArray<{ payload: Row }> }) {
  const row = payload?.[0]?.payload;
  if (!active || row === undefined) return null;
  return (
    <div className="max-w-60 rounded-md bg-tooltip-bg px-3 py-2 text-caption text-on-primary">
      <p className="font-semibold">
        {row.month}
        {row.skipped ? " · skipped" : ""}
      </p>
      <p>Saved to date {formatHuf(row.saved)}</p>
    </div>
  );
}

/**
 * Figma 06 chart: saved-to-date bars; a skipped month is a grey bar with a dashed amber outline
 * (the total did not grow). `compact` is the plan-review thumbnail: no axes, no tooltip.
 * Hidden from screen readers: the month table carries the same values (AC4).
 */
export function SavedChart({ months, compact = false }: { months: BacktestMonthOut[]; compact?: boolean }) {
  const rows: Row[] = months.map((m) => ({
    month: formatMonth(m.month),
    label: monthName(m.month),
    saved: m.saved_to_date,
    skipped: m.skipped,
  }));
  return (
    <div aria-hidden="true" className={compact ? "h-24" : "h-72"}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} accessibilityLayer={!compact} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          {compact ? null : <CartesianGrid vertical={false} stroke="var(--color-chart-grid)" />}
          {compact ? null : <XAxis dataKey="label" tickLine={false} axisLine={false} />}
          {compact ? null : <YAxis tickFormatter={formatCompact} tickLine={false} axisLine={false} width={48} />}
          {compact ? null : <Tooltip content={SavedTooltip} cursor={{ fill: "var(--color-surface-hover)" }} />}
          <Bar dataKey="saved" radius={[4, 4, 0, 0]}>
            {rows.map((row) => (
              <Cell
                key={row.month}
                fill={row.skipped ? "var(--color-chart-income)" : "var(--color-chart-saved)"}
                stroke={row.skipped ? "var(--color-chart-skipped)" : "none"}
                strokeDasharray={row.skipped ? "4 3" : undefined}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

`--color-chart-income` (#cbd5e1) is the Figma grey used for skipped bars. Recharts 3 still supports `Cell`; if the installed version deprecates it, use the `shape` prop with the same fill/stroke rule.

- [ ] **Step 5: Plan review screen**

`frontend/src/screens/plan-review/machineSummary.ts`:

```ts
import type { TimeMachineOut } from "../../api/types";
import { formatHuf } from "../../format";

/** "147,000 HUF saved · 1 month skipped" (plan review card and summary panels). */
export function machineSummary(machine: TimeMachineOut): string {
  const skipped = machine.skipped_months.length;
  return `${formatHuf(machine.total_saved)} saved · ${skipped} ${skipped === 1 ? "month" : "months"} skipped`;
}
```

`frontend/src/screens/plan-review/PlanReviewScreen.tsx`:

```tsx
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { ApiError } from "../../api/client";
import { useEditPlan, usePlan, usePlanAction, useTimeMachine } from "../../api/hooks";
import type { PlanOut } from "../../api/types";
import { Badge, confidenceBadge } from "../../components/Badge";
import { Button, buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { Icon } from "../../components/Icon";
import { PlanItemCard } from "../../components/PlanItemCard";
import { SavedChart } from "../../components/SavedChart";
import { SummaryPanel } from "../../components/SummaryPanel";
import { TextField } from "../../components/TextField";
import { formatHuf, parseHuf } from "../../format";
import { machineSummary } from "./machineSummary";

function Facts({ plan }: { plan: PlanOut }) {
  const rows: [string, string][] = [
    ["Median monthly surplus", plan.median_surplus === null ? "Your own estimate" : formatHuf(plan.median_surplus)],
    ["Share saved", `${plan.share_percent}%`],
    ["Months analysed", String(plan.months_of_data)],
    ["Risk score", String(plan.risk_score)],
    ["Minimum balance kept", formatHuf(plan.min_balance)],
  ];
  return (
    <dl className="mt-4 space-y-2">
      {rows.map(([term, value]) => (
        <div key={term} className="flex justify-between text-body">
          <dt className="text-text-muted">{term}</dt>
          <dd className="font-semibold">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function SaveLess({ plan }: { plan: PlanOut }) {
  const edit = useEditPlan(plan.id);
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
    edit.mutate(amount);
  }

  const serverError = edit.error instanceof ApiError && edit.error.field === "monthly_amount" ? edit.error.message : null;
  return (
    <Card title="Want to save less?">
      <form className="flex flex-col gap-3 md:flex-row md:items-start" onSubmit={submit} noValidate>
        <TextField
          className="flex-1"
          label="Monthly amount"
          inputMode="numeric"
          suffix="HUF"
          value={text}
          error={invalid ? "Enter a positive whole amount in forints." : serverError}
          hint={`Between 1 and ${formatHuf(plan.proposed_amount)}. A lower amount creates a revised plan; nothing runs until you accept it.`}
          onChange={(e) => setText(e.target.value)}
        />
        <Button type="submit" variant="secondary" className="md:mt-7" disabled={edit.isPending}>
          Update plan
        </Button>
      </form>
      {serverError ? null : <ErrorMessage error={edit.error} />}
    </Card>
  );
}

/** Figma 05 Plan review (7:282) and 05b low confidence (10:709), step 3 of 4. */
export function PlanReviewScreen() {
  const planId = Number(useParams().planId);
  const navigate = useNavigate();
  const plan = usePlan(planId);
  const machine = useTimeMachine(planId);
  const reject = usePlanAction("reject");
  const data = plan.data;
  const proposed = data?.status === "proposed";

  return (
    <FlowLayout step={3} title="Plan review" backTo={`/plans/${planId}/analysis`} wide>
      <ErrorMessage error={plan.error} />
      {data ? (
        <div className="flex flex-col gap-6 lg:flex-row">
          <div className="flex-1 space-y-6">
            <header>
              <h1 className="text-h1">Your savings plan</h1>
              <p className="text-text-muted">
                {proposed
                  ? `Proposed ${data.created_on}. Not active until you sign the mandate.`
                  : `This plan is ${data.status}.`}
              </p>
              {proposed ? null : (
                <Link to="/plan" className={`${buttonClass("secondary")} mt-3`}>
                  Go to your savings plan
                </Link>
              )}
            </header>
            <Card title="Why this amount">
              <p className="text-body">{data.explanations[0]}</p>
              <Facts plan={data} />
            </Card>
            {data.per_transfer_approval ? (
              <section className="flex gap-3 rounded-lg border border-warning bg-warning-bg p-4 text-warning">
                <Icon name="alert" />
                <div>
                  <h2 className="text-h3">Every transfer needs your approval</h2>
                  {data.explanations.slice(1).map((text) => (
                    <p key={text} className="text-body">
                      {text}
                    </p>
                  ))}
                </div>
              </section>
            ) : null}
            <Card title="Where the money goes, in priority order">
              <ul aria-label="Plan items" className="space-y-3">
                {data.items.map((item) => (
                  <PlanItemCard key={item.position} item={item} number={item.position + 1} />
                ))}
              </ul>
              <p className="mt-3 text-caption text-text-muted">
                Risk score {data.risk_score} from your answers: no product above risk {data.risk_score} is used. Items
                with nothing left to fund are not shown.
              </p>
            </Card>
            <Card>
              <h2 className="flex items-center gap-2 text-h3">
                <Icon name="history" />
                Time machine: this plan on your last {machine.data?.months_replayed ?? ""} months
              </h2>
              <ErrorMessage error={machine.error} />
              {machine.data ? (
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <SavedChart months={machine.data.months} compact />
                  <div>
                    <p className="text-h2">{machineSummary(machine.data)}</p>
                    <p className="mt-2 text-body text-text-muted">Past behaviour only, not a forecast.</p>
                  </div>
                </div>
              ) : null}
              <Link to={`/plans/${planId}/time-machine`} className={`${buttonClass("ghost")} mt-4`}>
                <Icon name="chevron-right" />
                See month by month
              </Link>
            </Card>
            {proposed ? <SaveLess plan={data} /> : null}
            {proposed ? (
              <div>
                <ErrorMessage error={reject.error} />
                <Button variant="danger" disabled={reject.isPending} onClick={() => reject.mutate(planId, { onSuccess: () => navigate("/") })}>
                  Reject plan
                </Button>
              </div>
            ) : null}
          </div>
          {proposed ? (
            <SummaryPanel
              label="Monthly amount"
              value={
                <>
                  <span>{formatHuf(data.monthly_amount)}</span> <span className="text-body font-normal text-text-muted">/ month</span>
                </>
              }
              badge={<Badge tone={confidenceBadge(data.confidence).tone}>{confidenceBadge(data.confidence).label}</Badge>}
              details={
                <dl className="space-y-2 text-body">
                  {machine.data ? (
                    <div>
                      <dt className="text-caption text-text-muted">Time machine, last {machine.data.months_replayed} months</dt>
                      <dd className="font-semibold">{machineSummary(machine.data)}</dd>
                    </div>
                  ) : null}
                  <div className="flex justify-between">
                    <dt className="text-text-muted">First transfer</dt>
                    <dd className="font-semibold">{data.next_transfer_on}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-text-muted">Minimum balance kept</dt>
                    <dd className="font-semibold">{formatHuf(data.min_balance)}</dd>
                  </div>
                </dl>
              }
              action={
                <Link to={`/plans/${planId}/mandate`} className={buttonClass("primary")}>
                  Continue to mandate
                </Link>
              }
              note="Nothing runs until you sign the mandate."
            />
          ) : null}
        </div>
      ) : null}
    </FlowLayout>
  );
}
```

`skipped_months.length` counts the months the API listed; `item.position + 1` is a display number. Neither is money. The amount and "/ month" are separate spans so tests (and screen readers) find the amount on its own.

When the PATCH succeeds, `SaveLess` keeps the typed text; the panel and items update from the new `PlanOut`.

In `frontend/src/App.tsx`, add the flow route `<Route path="/plans/:planId" element={<PlanReviewScreen />} />`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/screens/plan-review`
Expected: 9 passed.

- [ ] **Step 7: Docs**

`docs/traceability.md`: AC1 append `; frontend/src/screens/plan-review/PlanReviewScreen.test.tsx::test_ac1_plan_review_shows_73500_with_high_confidence`; AC2 append `; frontend/src/screens/plan-review/PlanReviewScreen.test.tsx::test_ac2_emergency_fund_is_the_first_item`; AC6 append `; frontend/src/screens/plan-review/PlanReviewScreen.test.tsx::test_ac6_low_confidence_plan_says_every_transfer_needs_approval`; AC7 append `; frontend/src/screens/plan-review/PlanReviewScreen.test.tsx::test_ac7_rejecting_goes_home_without_orders`; AC8 append `; frontend/src/screens/plan-review/PlanReviewScreen.test.tsx::test_ac8_amount_above_proposal_shows_the_server_message`.

`CHANGELOG.md`, `### Added`: `- Plan review (Figma 05, 05b): explanation and plan facts, priority-ordered items, time machine summary, lower-the-amount and reject, sticky summary panel with the confidence level (AC1, AC2, AC6–AC8).`

Run: `cd frontend && npm run fmt && npm run lint && cd .. && make docs-check`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): plan review screen from figma 05 (AC1, AC2, AC6-AC8)`

---

### Task 15: Time machine (06), sub-view of step 3 (AC4)

Deliverable: Figma 06 (`7:452`) at `/plans/:planId/time-machine`: stat tiles (saved, transfers made, months skipped), the saved-to-date chart with skipped months styled, the "Skipped months" list with the backend notes, a month-by-month table, and "Continue to mandate".

**Files:**
- Create: `frontend/src/screens/time-machine/TimeMachineScreen.tsx`, `frontend/src/screens/time-machine/TimeMachineScreen.test.tsx`
- Modify: `frontend/src/App.tsx`, `docs/traceability.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `usePlan`, `useTimeMachine` (Task 14), `SavedChart` (Task 14), `FlowLayout`, `StatTile`, `Card`, `Badge`, `Icon`, `buttonClass`, `ErrorMessage`, `formatHuf`, `formatMonth` (Tasks 7–8), fixtures `PLAN`, `MACHINE`.
- Produces: `TimeMachineScreen` at `/plans/:planId/time-machine` (FlowLayout step 3 "Plan review · time machine", back `/plans/:planId`).

- [ ] **Step 1: Write the failing test**

`frontend/src/screens/time-machine/TimeMachineScreen.test.tsx`:

```tsx
import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import { MACHINE, PLAN, plan } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { TimeMachineScreen } from "./TimeMachineScreen";

const NOTE = MACHINE.months[2]?.note ?? "";

function start(current = PLAN) {
  mockApi({
    "GET /api/plans/7": { body: current },
    "GET /api/plans/7/time-machine": { body: MACHINE },
  });
  renderScreen(<TimeMachineScreen />, { path: "/plans/:planId/time-machine", url: "/plans/7/time-machine" });
}

test("test_ac4_time_machine_flags_skipped_month", async () => {
  start();
  const table = await screen.findByRole("table", { name: "Saved to date, month by month" });
  const skippedRow = within(table).getByRole("row", { name: /2025-12/ });
  expect(within(skippedRow).getByText("Skipped")).toBeInTheDocument();
  expect(within(skippedRow).getByText("147,000 HUF")).toBeInTheDocument(); // total unchanged
  const list = screen.getByRole("list", { name: "Skipped months" });
  expect(within(list).getByText(NOTE)).toBeInTheDocument();
});

test("test_ac4_time_machine_shows_totals_from_the_api", async () => {
  start();
  const tiles = await screen.findByRole("region", { name: "Totals" });
  expect(within(tiles).getByText("147,000 HUF")).toBeInTheDocument();
  expect(within(tiles).getByText("2 of 3")).toBeInTheDocument();
  expect(screen.getByText("past behaviour only, not a forecast.", { exact: false })).toBeInTheDocument();
});

test("continues to the mandate only for a proposed plan", async () => {
  start();
  expect(await screen.findByRole("link", { name: "Continue to mandate" })).toHaveAttribute("href", "/plans/7/mandate");
});

test("an accepted plan shows the replay without signing", async () => {
  start(plan({ status: "accepted" }));
  await screen.findByRole("table", { name: "Saved to date, month by month" });
  expect(screen.queryByRole("link", { name: "Continue to mandate" })).toBeNull();
});
```

The totals are scoped to `<section aria-label="Totals">` because the table rows also show 147,000 HUF.

- [ ] **Step 2: Run it to verify it fails**

Run: `cd frontend && npx vitest run src/screens/time-machine`
Expected: FAIL — `./TimeMachineScreen` unresolved.

- [ ] **Step 3: Implement the screen**

`frontend/src/screens/time-machine/TimeMachineScreen.tsx`:

```tsx
import { Link, useParams } from "react-router";
import { usePlan, useTimeMachine } from "../../api/hooks";
import { Badge } from "../../components/Badge";
import { buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { Icon } from "../../components/Icon";
import { SavedChart } from "../../components/SavedChart";
import { StatTile } from "../../components/StatTile";
import { formatHuf, formatMonth } from "../../format";

/** Figma 06 Financial time machine (7:452), AC4. Past behaviour only, not a forecast. */
export function TimeMachineScreen() {
  const planId = Number(useParams().planId);
  const plan = usePlan(planId);
  const machine = useTimeMachine(planId);
  const data = machine.data;
  const minimum = plan.data ? formatHuf(plan.data.min_balance) : "";
  const tableTitle = "Saved to date, month by month";

  return (
    <FlowLayout step={3} title="Plan review · time machine" backTo={`/plans/${planId}`} wide>
      <div className="space-y-6">
        <header>
          <h1 className="text-h1">Financial time machine</h1>
          <p className="text-text-muted">
            What would have happened if this plan had run on your last {data?.months_replayed ?? ""} months of real
            transactions? This shows past behaviour only, not a forecast.
          </p>
        </header>
        <ErrorMessage error={machine.error ?? plan.error} />
        {data && plan.data ? (
          <>
            <section aria-label="Totals" className="grid gap-4 md:grid-cols-3">
              <StatTile
                label={`Saved over ${data.months_replayed} months`}
                value={formatHuf(data.total_saved)}
                caption={`${formatHuf(plan.data.monthly_amount)} a month when it ran`}
              />
              <StatTile
                label="Transfers made"
                value={`${data.transfers_made} of ${data.months_replayed}`}
                caption={`Each one within the ${minimum} minimum`}
              />
              <StatTile
                label="Months skipped"
                value={String(data.skipped_months.length)}
                caption={data.skipped_months.map(formatMonth).join(" and ") || "None"}
              />
            </section>
            <Card title={tableTitle}>
              <SavedChart months={data.months} />
              <p className="mt-2 text-caption text-text-muted">Value labels appear on hover or keyboard focus, not on every bar.</p>
              <details className="mt-4">
                <summary className="flex min-h-touch cursor-pointer items-center text-body font-semibold text-primary">
                  See month by month
                </summary>
                <table className="mt-2 w-full text-left text-body">
                  <caption className="sr-only">{tableTitle}</caption>
                  <thead>
                    <tr className="text-caption text-text-muted">
                      <th className="py-2">Month</th>
                      <th>Balance before</th>
                      <th>Transfer</th>
                      <th>Saved to date</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.months.map((m) => (
                      <tr key={m.month} className="border-t border-border">
                        <th scope="row" className="py-2 text-left font-normal">
                          {formatMonth(m.month)}
                        </th>
                        <td>{formatHuf(m.balance_before_transfer)}</td>
                        <td>{formatHuf(m.transfer)}</td>
                        <td>{formatHuf(m.saved_to_date)}</td>
                        <td>{m.skipped ? <Badge tone="warning">Skipped</Badge> : <Badge tone="success">Transferred</Badge>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            </Card>
            {data.skipped_months.length > 0 ? (
              <Card>
                <h2 className="mb-4 flex items-center gap-2 text-h3">
                  Skipped months <Badge tone="warning">{data.skipped_months.length}</Badge>
                </h2>
                <ul aria-label="Skipped months" className="space-y-2">
                  {data.months
                    .filter((m) => m.note !== null)
                    .map((m) => (
                      <li key={m.month} className="flex gap-3 rounded-md bg-warning-bg p-3 text-body">
                        <Icon name="alert" className="size-5 text-warning" />
                        {m.note}
                      </li>
                    ))}
                </ul>
              </Card>
            ) : null}
            {plan.data.status === "proposed" ? (
              <div className="flex justify-end">
                <Link to={`/plans/${planId}/mandate`} className={buttonClass("primary")}>
                  Continue to mandate
                </Link>
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </FlowLayout>
  );
}
```

The skipped list shows the backend `note` of each skipped month verbatim (golden rule 2). The row header (`<th scope="row">`) gives each row its accessible name, so the test can find the row by month.

In `frontend/src/App.tsx`, add the flow route `<Route path="/plans/:planId/time-machine" element={<TimeMachineScreen />} />`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/screens/time-machine`
Expected: 4 passed. If `getByRole("row", { name: /2025-12/ })` finds no row, the accessible name of a `<tr>` in your Testing Library version comes from all its cells; the regex still matches "2025-12 …". Do not remove the assertion.

- [ ] **Step 5: Docs**

`docs/traceability.md`, AC4: append `; frontend/src/screens/time-machine/TimeMachineScreen.test.tsx::test_ac4_time_machine_flags_skipped_month`; change Verification to `automated + manual` once Task 18 adds the manual check.

`CHANGELOG.md`, `### Added`: `- Time machine (Figma 06): saved-to-date chart with skipped months (grey bar, dashed amber outline), skipped-month notes from the backend and a month table (AC4).`

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 6: Suggested commit (user commits)**

`feat(frontend): time machine screen from figma 06 (AC4)`

---

### Task 16: Mandate (07) and password confirmation (07b), step 4 (AC7)

Deliverable: Figma 07 (`8:422`) and 07b (`8:550`) at `/plans/:planId/mandate`: mandate terms and clauses from the API, consent checkbox, "What happens when you sign", the summary panel with "Sign mandate", and the "Confirm with your password" modal that calls `POST /api/plans/{id}/accept {password}`. A signed mandate shows its version and date and no second signing.

**Files:**
- Create: `frontend/src/screens/mandate/{MandateScreen,ConfirmSignModal}.tsx`, `frontend/src/screens/mandate/MandateScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `docs/traceability.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `GET /api/plans/{id}/mandate` (`MandateOut`, `version` = the version signing creates while unsigned), `POST /api/plans/{id}/accept` (`{password}`; 403 `Incorrect password.`; 409), `usePlan`, `useTimeMachine`, `machineSummary` (`screens/plan-review/machineSummary.ts`, Task 14), `FlowLayout`, `SummaryPanel`, `Modal` (Task 8), `Card`, `Checkbox`, `Badge`, `confidenceBadge`, `TextField`, `Button`, `buttonClass`, `Kbd`, `ErrorMessage`, `formatHuf`, `formatDay` (Task 7).
- Produces: `useMandate(planId)`, `useAcceptPlan(planId)` (mutate `password: string`; invalidates plans, mandate, activity, account); `ConfirmSignModal({ mandate, onClose, onConfirm(password), pending, error })`; `MandateScreen` at `/plans/:planId/mandate` (FlowLayout step 4 "Mandate", back `/plans/:planId`). After signing it navigates to `/plan`.

- [ ] **Step 1: Write the failing tests**

`frontend/src/screens/mandate/MandateScreen.test.tsx`:

```tsx
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { MandateOut } from "../../api/types";
import { MACHINE, PLAN, plan } from "../../test/fixtures";
import { mockApi, renderScreen, type Handler } from "../../test/render";
import { MandateScreen } from "./MandateScreen";

const CLAUSE_1 =
  "SaverAI may transfer only to the products listed in this mandate, at most the monthly maximum in total per calendar month.";
const UNSIGNED: MandateOut = {
  status: "unsigned",
  version: 1,
  signed_at: null,
  max_monthly_amount: 73_500,
  min_balance: 100_000,
  per_transfer_approval: false,
  products: [{ id: 1, name: "Short government bond fund", risk_level: 2, liquid: true }],
  clauses: [
    { number: 1, text: CLAUSE_1 },
    { number: 4, text: "No transfer runs while the mandate is paused." },
  ],
};

function start(mandate: MandateOut = UNSIGNED, accept: Handler = { body: plan({ status: "accepted", mandate_version: 1 }) }) {
  const calls = mockApi({
    "GET /api/plans/7": { body: mandate.status === "unsigned" ? PLAN : plan({ status: "accepted", mandate_version: 1 }) },
    "GET /api/plans/7/time-machine": { body: MACHINE },
    "GET /api/plans/7/mandate": { body: mandate },
    "POST /api/plans/7/accept": accept,
  });
  renderScreen(<MandateScreen />, { path: "/plans/:planId/mandate", url: "/plans/7/mandate" });
  return { calls, user: userEvent.setup() };
}

async function openModal(user: ReturnType<typeof userEvent.setup>) {
  const sign = await screen.findByRole("button", { name: "Sign mandate" });
  expect(sign).toBeDisabled();
  await user.click(screen.getByRole("checkbox", { name: "I have read the mandate and authorise these recurring orders." }));
  await user.click(sign);
  return screen.getByRole("dialog", { name: "Confirm with your password" });
}

test("shows the terms and clauses from the API", async () => {
  start();
  expect(await screen.findByRole("heading", { name: "Mandate · version 1" })).toBeInTheDocument();
  expect(screen.getByText(CLAUSE_1)).toBeInTheDocument();
  expect(screen.getByText("Short government bond fund")).toBeInTheDocument();
  expect(screen.getByText("Off (high confidence)")).toBeInTheDocument();
});

test("test_ac7_signing_needs_consent_then_password", async () => {
  const { calls, user } = start();
  const dialog = await openModal(user);
  expect(within(dialog).getByText(/up to 73,500 HUF a month to the Short government bond fund/)).toBeInTheDocument();
  await user.type(within(dialog).getByLabelText("Password"), "secret");
  await user.click(within(dialog).getByRole("button", { name: "Confirm and sign" }));
  expect(await screen.findByText("Navigated to /plan")).toBeInTheDocument();
  expect(calls.filter((c) => c.method === "POST")).toEqual([
    expect.objectContaining({ path: "/api/plans/7/accept", body: { password: "secret" } }),
  ]);
});

test("a wrong password keeps the modal open and shows the message", async () => {
  const { user } = start(UNSIGNED, { status: 403, body: { detail: "Incorrect password." } });
  const dialog = await openModal(user);
  await user.type(within(dialog).getByLabelText("Password"), "wrong");
  await user.keyboard("{Enter}");
  expect(await within(dialog).findByRole("alert")).toHaveTextContent("Incorrect password.");
  expect(screen.getByRole("dialog", { name: "Confirm with your password" })).toBeInTheDocument();
});

test("test_ac7_confirm_button_is_disabled_while_signing", async () => {
  const { calls, user } = start(UNSIGNED, () => new Promise(() => undefined)); // never answers
  const dialog = await openModal(user);
  await user.type(within(dialog).getByLabelText("Password"), "secret");
  const confirm = within(dialog).getByRole("button", { name: "Confirm and sign" });
  await user.click(confirm);
  await user.click(confirm);
  await user.keyboard("{Enter}");
  expect(confirm).toBeDisabled();
  expect(calls.filter((c) => c.method === "POST")).toHaveLength(1);
});

test("Esc closes the modal without signing", async () => {
  const { calls, user } = start();
  await openModal(user);
  await user.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(calls.filter((c) => c.method === "POST")).toEqual([]);
});

test("test_ac7_signed_mandate_offers_no_second_signing", async () => {
  start({ ...UNSIGNED, status: "active", signed_at: "2026-10-08T12:00:00Z" });
  expect(await screen.findByText("Version 1, signed 2026-10-08")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Sign mandate" })).toBeNull();
  expect(screen.getByRole("link", { name: "Go to your savings plan" })).toHaveAttribute("href", "/plan");
});
```

`mockApi` handlers may return a promise; one that never resolves keeps the mutation pending.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd frontend && npx vitest run src/screens/mandate`
Expected: FAIL — `./MandateScreen` unresolved.

- [ ] **Step 3: Hooks**

Append to `frontend/src/api/hooks.ts` (types `MandateOut` added to the import):

```ts
export function useMandate(planId: number) {
  return useQuery({ queryKey: keys.mandate(planId), queryFn: () => apiFetch<MandateOut>(`/api/plans/${planId}/mandate`) });
}

/** Sign the mandate with the customer's password (ADR-0004). Accepting twice creates nothing new (AC7). */
export function useAcceptPlan(planId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (password: string) =>
      apiFetch<PlanOut>(`/api/plans/${planId}/accept`, { method: "POST", body: { password } }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.activity });
      await client.invalidateQueries({ queryKey: keys.account });
    },
  });
}
```

(`keys.plans` is a prefix of `keys.plan(id)`, `keys.mandate(id)` and `keys.activePlan`, so one call refreshes them all.)

- [ ] **Step 4: The modal**

`frontend/src/screens/mandate/ConfirmSignModal.tsx`:

```tsx
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
          You are signing mandate version {mandate.version}: up to {formatHuf(mandate.max_monthly_amount)} a month to the{" "}
          {products}, always keeping at least {formatHuf(mandate.min_balance)} on your account.
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
```

- [ ] **Step 5: The screen**

`frontend/src/screens/mandate/MandateScreen.tsx`:

```tsx
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { useAcceptPlan, useMandate, usePlan, useTimeMachine } from "../../api/hooks";
import type { MandateOut, PlanOut } from "../../api/types";
import { Badge, confidenceBadge } from "../../components/Badge";
import { Button, buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { Checkbox } from "../../components/Checkbox";
import { ErrorMessage } from "../../components/ErrorMessage";
import { FlowLayout } from "../../components/FlowLayout";
import { SummaryPanel } from "../../components/SummaryPanel";
import { formatDay, formatHuf } from "../../format";
import { machineSummary } from "../plan-review/machineSummary";
import { ConfirmSignModal } from "./ConfirmSignModal";

const CONSENT = "I have read the mandate and authorise these recurring orders.";

function Terms({ mandate }: { mandate: MandateOut }) {
  const rows: [string, string][] = [
    ["Monthly maximum (total)", formatHuf(mandate.max_monthly_amount)],
    ["Minimum balance kept", formatHuf(mandate.min_balance)],
    ["Allowed products", mandate.products.map((p) => p.name).join(", ")],
    ["Per-transfer approval", mandate.per_transfer_approval ? "On (low confidence)" : "Off (high confidence)"],
  ];
  return (
    <dl className="space-y-2 rounded-md bg-surface-hover p-4">
      {rows.map(([term, value]) => (
        <div key={term} className="flex justify-between gap-4 text-body">
          <dt className="text-text-muted">{term}</dt>
          <dd className="text-right font-semibold">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function WhatHappens({ plan }: { plan: PlanOut }) {
  const lines = [
    "Your recurring orders are created once. Signing again creates no duplicates.",
    `The first transfers run on ${plan.next_transfer_on}, each checked against this mandate first.`,
    "You can pause at any time (§4).",
    "Changing the amount later creates a new mandate version; this version stays in the log.",
  ];
  return (
    <Card title="What happens when you sign">
      <ul className="list-disc space-y-1 pl-5 text-body">
        {lines.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </Card>
  );
}

/** Figma 07 Mandate (8:422) and 07b password confirmation (8:550), step 4 of 4 (AC7). */
export function MandateScreen() {
  const planId = Number(useParams().planId);
  const navigate = useNavigate();
  const plan = usePlan(planId);
  const machine = useTimeMachine(planId);
  const mandate = useMandate(planId);
  const accept = useAcceptPlan(planId);
  const [consent, setConsent] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const m = mandate.data;
  const p = plan.data;
  const unsigned = m?.status === "unsigned";

  return (
    <FlowLayout step={4} title="Mandate" backTo={`/plans/${planId}`} wide>
      <ErrorMessage error={mandate.error ?? plan.error} />
      {m && p ? (
        <div className="flex flex-col gap-6 lg:flex-row">
          <div className="flex-1 space-y-6">
            <header>
              <h1 className="text-h1">{unsigned ? "Sign your mandate" : "Your mandate"}</h1>
              <p className="text-text-muted">
                Orders run only within these limits. Every executed order is logged with the mandate version and the clause
                that allowed it.
              </p>
            </header>
            <Card>
              <h2 className="mb-4 text-h2">Mandate · version {m.version}</h2>
              {unsigned ? null : (
                <p className="mb-4 text-body font-semibold">
                  Version {m.version}, signed {formatDay(m.signed_at ?? "")}
                </p>
              )}
              <Terms mandate={m} />
              <ol className="mt-4 space-y-3">
                {m.clauses.map((clause) => (
                  <li key={clause.number} className="flex gap-3 text-body">
                    <span className="rounded-sm bg-surface-hover px-2 py-0.5 text-caption font-semibold">§{clause.number}</span>
                    <span>{clause.text}</span>
                  </li>
                ))}
              </ol>
              {unsigned ? (
                <div className="mt-4 rounded-md border border-border">
                  <Checkbox label={CONSENT} checked={consent} onChange={(e) => setConsent(e.target.checked)} />
                </div>
              ) : (
                <Link to="/plan" className={`${buttonClass("secondary")} mt-4`}>
                  Go to your savings plan
                </Link>
              )}
            </Card>
            {unsigned ? <WhatHappens plan={p} /> : null}
          </div>
          {unsigned ? (
            <SummaryPanel
              label="You are signing"
              value={
                <>
                  <span>{formatHuf(m.max_monthly_amount)}</span> <span className="text-body font-normal text-text-muted">/ month</span>
                </>
              }
              badge={<Badge tone={confidenceBadge(p.confidence).tone}>{confidenceBadge(p.confidence).label}</Badge>}
              details={
                <dl className="space-y-2 text-body">
                  {machine.data ? (
                    <div>
                      <dt className="text-caption text-text-muted">Time machine, last {machine.data.months_replayed} months</dt>
                      <dd className="font-semibold">{machineSummary(machine.data)}</dd>
                    </div>
                  ) : null}
                  <div className="flex justify-between">
                    <dt className="text-text-muted">First transfer</dt>
                    <dd className="font-semibold">{p.next_transfer_on}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-text-muted">Minimum balance kept</dt>
                    <dd className="font-semibold">{formatHuf(m.min_balance)}</dd>
                  </div>
                </dl>
              }
              action={
                <Button disabled={!consent} onClick={() => setConfirming(true)}>
                  Sign mandate
                </Button>
              }
              note="You confirm with your password in the next step."
            />
          ) : null}
        </div>
      ) : null}
      {confirming && m ? (
        <ConfirmSignModal
          mandate={m}
          pending={accept.isPending}
          error={accept.error}
          onClose={() => {
            accept.reset();
            setConfirming(false);
          }}
          onConfirm={(password) => accept.mutate(password, { onSuccess: () => navigate("/plan") })}
        />
      ) : null}
    </FlowLayout>
  );
}
```

In `frontend/src/App.tsx`, add the flow route `<Route path="/plans/:planId/mandate" element={<MandateScreen />} />`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/screens/mandate`
Expected: 6 passed.

- [ ] **Step 7: Docs**

`docs/traceability.md`, AC7: append `; frontend/src/screens/mandate/MandateScreen.test.tsx::test_ac7_signing_needs_consent_then_password; frontend/src/screens/mandate/MandateScreen.test.tsx::test_ac7_confirm_button_is_disabled_while_signing; frontend/src/screens/mandate/MandateScreen.test.tsx::test_ac7_signed_mandate_offers_no_second_signing`.

`CHANGELOG.md`, `### Added`: `- Mandate screen (Figma 07) with terms and clauses from the API, consent, and password confirmation before signing (Figma 07b, ADR-0004); one request per confirmation (AC7).`

Run: `cd frontend && npm run fmt && npm run lint && cd .. && make docs-check`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): mandate signing with password confirmation (AC7)`

---

### Task 17: Active plan (08) and Activity: execution log, approve, pause, change amount (AC6, AC7)

Deliverable: Figma 08 (`8:708`) at `/plan` and the Activity page at `/activity`: stat tiles, recurring orders, the execution log (table from 768 px, stacked rows below; each row opens its audit details: mandate version, clause, idempotency key, logged at), "Approve" on transfers waiting for approval (AC6), "Pause plan" with a confirmation, and "Change amount", which proposes a revision (Task 4) and opens its review. A pending revision shows a banner with a link.

**Files:**
- Create: `frontend/src/components/ExecutionLog.tsx`, `frontend/src/components/ExecutionLog.test.tsx`
- Create: `frontend/src/screens/active-plan/{ActivePlanScreen,ChangeAmountModal}.tsx`, `frontend/src/screens/active-plan/ActivePlanScreen.test.tsx`
- Create: `frontend/src/screens/activity/ActivityScreen.tsx`, `frontend/src/screens/activity/ActivityScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `docs/traceability.md`, `CHANGELOG.md`, `docs/tasks.md`

**Interfaces:**
- Consumes: `GET /api/plans/active` (404 = none; `PlanOut.pending_revision` from Task 4), `GET /api/activity` (`ActivityOut[]`, Task 5), `POST /api/executions/{id}/approve`, `POST /api/plans/{id}/pause`, `POST /api/plans/{id}/revise {monthly_amount}` (Task 4); `useActivePlan` (Task 10), `usePlanAction` (Task 14); `Modal` (Task 8); `Card`, `StatTile`, `Badge`, `statusBadge`, `Button`, `buttonClass`, `TextField`, `Icon`, `ErrorMessage`, `formatHuf`, `formatDay`, `parseHuf` (Task 7).
- Produces: `useActivity()`, `useApproveExecution()` (mutate execution id), `useRevisePlan(planId)` (mutate amount → revision `PlanOut`); `ExecutionLog({ rows: ActivityOut[] })` (approval handled inside); `ChangeAmountModal({ plan, onClose })`; `ActivePlanScreen` at `/plan`; `ActivityScreen` at `/activity`.

- [ ] **Step 1: Write the failing tests**

`frontend/src/components/ExecutionLog.test.tsx`:

```tsx
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { ActivityOut } from "../api/types";
import { mockApi, renderScreen } from "../test/render";
import { ExecutionLog } from "./ExecutionLog";

const SCHEDULED: ActivityOut = {
  key: "scheduled-1-2026-11",
  on: "2026-11-01",
  title: "30,000 HUF to your emergency fund",
  amount: 30_000,
  status: "scheduled",
  mandate_version: 1,
  clause: "Will be checked against §1 and §2",
  idempotency_key: "order-1-2026-11",
  logged_at: null,
  execution_id: null,
};
const WAITING: ActivityOut = {
  ...SCHEDULED,
  key: "execution-5",
  on: "2026-10-01",
  status: "awaiting_approval",
  clause: "§3 · This transfer needs your approval.",
  idempotency_key: "order-1-2026-10",
  logged_at: "2026-10-06T12:00:00Z",
  execution_id: 5,
};

test("a row opens its audit details", async () => {
  mockApi({});
  renderScreen(<ExecutionLog rows={[SCHEDULED]} />);
  const user = userEvent.setup();
  const toggle = screen.getByRole("button", { name: "Audit details: 30,000 HUF to your emergency fund" });
  expect(toggle).toHaveAttribute("aria-expanded", "false");
  await user.click(toggle);
  expect(toggle).toHaveAttribute("aria-expanded", "true");
  expect(screen.getByText("order-1-2026-11")).toBeInTheDocument();
  expect(screen.getByText("Will be checked against §1 and §2")).toBeInTheDocument();
  expect(screen.getByText("Not run yet")).toBeInTheDocument();
  expect(screen.getByText("Scheduled")).toBeInTheDocument();
});

test("test_ac6_waiting_transfer_can_be_approved", async () => {
  const calls = mockApi({ "POST /api/executions/5/approve": { body: { id: 5, status: "executed" } } });
  renderScreen(<ExecutionLog rows={[WAITING]} />);
  const user = userEvent.setup();
  expect(screen.getByText("Needs approval")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Approve 30,000 HUF to your emergency fund" }));
  expect(calls.filter((c) => c.method === "POST").map((c) => c.path)).toEqual(["/api/executions/5/approve"]);
});

test("an empty log says so", () => {
  mockApi({});
  renderScreen(<ExecutionLog rows={[]} />);
  expect(screen.getByText("Nothing has happened yet.")).toBeInTheDocument();
  expect(within(document.body).queryByRole("table")).toBeNull();
});
```

`frontend/src/screens/active-plan/ActivePlanScreen.test.tsx`:

```tsx
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { PlanOut } from "../../api/types";
import { plan } from "../../test/fixtures";
import { mockApi, renderScreen, type Handler } from "../../test/render";
import { ActivePlanScreen } from "./ActivePlanScreen";

const ACTIVE = plan({ status: "accepted", mandate_version: 1, signed_on: "2026-10-08" });

function start(active: PlanOut | null = ACTIVE, routes: Record<string, Handler> = {}) {
  const calls = mockApi({
    "GET /api/plans/active": active === null ? { status: 404, body: { detail: "No active plan." } } : { body: active },
    "GET /api/activity": { body: [] },
    ...routes,
  });
  renderScreen(<ActivePlanScreen />, { path: "/plan" });
  return { calls, user: userEvent.setup() };
}

test("shows the plan facts and recurring orders from the API", async () => {
  start();
  expect(await screen.findByText("Accepted 2026-10-08 under mandate version 1.")).toBeInTheDocument();
  expect(screen.getByText("Version 1")).toBeInTheDocument();
  expect(screen.getByText("3 recurring orders")).toBeInTheDocument();
  const orders = screen.getByRole("list", { name: "Recurring orders" });
  expect(within(orders).getAllByRole("listitem")).toHaveLength(3);
  expect(within(orders).getByText("Short government bond fund · until 2027-08-01")).toBeInTheDocument();
});

test("shows the empty state when there is no active plan", async () => {
  start(null);
  expect(await screen.findByRole("link", { name: "Start a savings plan" })).toHaveAttribute("href", "/questionnaire");
});

test("pause asks for confirmation, then pauses", async () => {
  const { calls, user } = start(ACTIVE, { "POST /api/plans/7/pause": { body: plan({ status: "paused" }) } });
  await user.click(await screen.findByRole("button", { name: "Pause plan" }));
  const dialog = screen.getByRole("dialog", { name: "Pause your savings plan?" });
  await user.click(within(dialog).getByRole("button", { name: "Pause plan" }));
  expect(calls.filter((c) => c.method === "POST").map((c) => c.path)).toEqual(["/api/plans/7/pause"]);
});

test("change amount proposes a revision and opens its review", async () => {
  const { calls, user } = start(ACTIVE, {
    "POST /api/plans/7/revise": { body: plan({ id: 12, revises: 7, monthly_amount: 50_000 }) },
  });
  await user.click(await screen.findByRole("button", { name: "Change amount" }));
  const dialog = screen.getByRole("dialog", { name: "Change the monthly amount" });
  await user.clear(within(dialog).getByLabelText("New monthly amount"));
  await user.type(within(dialog).getByLabelText("New monthly amount"), "50000");
  await user.click(within(dialog).getByRole("button", { name: "Propose new amount" }));
  expect(await screen.findByText("Navigated to /plans/12")).toBeInTheDocument();
  expect(calls.find((c) => c.method === "POST")?.body).toEqual({ monthly_amount: 50_000 });
});

test("a revision error is shown in the change-amount modal", async () => {
  const { user } = start(ACTIVE, {
    "POST /api/plans/7/revise": { status: 409, body: { detail: "A revised plan is already waiting for your signature." } },
  });
  await user.click(await screen.findByRole("button", { name: "Change amount" }));
  const dialog = screen.getByRole("dialog", { name: "Change the monthly amount" });
  await user.click(within(dialog).getByRole("button", { name: "Propose new amount" }));
  expect(await within(dialog).findByRole("alert")).toHaveTextContent("A revised plan is already waiting for your signature.");
});

test("a pending revision links to its review", async () => {
  start(plan({ ...ACTIVE, pending_revision: 12 }));
  expect(await screen.findByRole("link", { name: "Review the new amount" })).toHaveAttribute("href", "/plans/12");
});

test("a paused plan offers no pause or change", async () => {
  start(plan({ ...ACTIVE, status: "paused" }));
  await screen.findByText("Paused");
  expect(screen.queryByRole("button", { name: "Pause plan" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Change amount" })).toBeNull();
});
```

`frontend/src/screens/activity/ActivityScreen.test.tsx`:

```tsx
import { screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { mockApi, renderScreen } from "../../test/render";
import { ActivityScreen } from "./ActivityScreen";

test("lists the activity rows from the API", async () => {
  mockApi({
    "GET /api/activity": {
      body: [
        {
          key: "event-1",
          on: "2026-10-08",
          title: "Plan proposed: 73,500 HUF a month",
          amount: 73_500,
          status: "proposed",
          mandate_version: null,
          clause: null,
          idempotency_key: null,
          logged_at: "2026-10-08T12:00:00Z",
          execution_id: null,
        },
      ],
    },
  });
  renderScreen(<ActivityScreen />, { path: "/activity" });
  expect(await screen.findByRole("heading", { name: "Activity" })).toBeInTheDocument();
  expect(await screen.findByText("Plan proposed: 73,500 HUF a month")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd frontend && npx vitest run src/components/ExecutionLog.test.tsx src/screens/active-plan src/screens/activity`
Expected: FAIL — modules unresolved.

- [ ] **Step 3: Hooks**

Append to `frontend/src/api/hooks.ts` (types `ActivityOut, ExecutionOut` added to the import):

```ts
export function useActivity() {
  return useQuery({ queryKey: keys.activity, queryFn: () => apiFetch<ActivityOut[]>("/api/activity") });
}

/** Approve one transfer of a low-confidence plan (AC6). */
export function useApproveExecution() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (executionId: number) => apiFetch<ExecutionOut>(`/api/executions/${executionId}/approve`, { method: "POST" }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.activity });
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.account });
    },
  });
}

/** Propose a new amount for the active plan; nothing changes until it is signed (ADR-0004). */
export function useRevisePlan(planId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (monthlyAmount: number) =>
      apiFetch<PlanOut>(`/api/plans/${planId}/revise`, { method: "POST", body: { monthly_amount: monthlyAmount } }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.activity });
    },
  });
}
```

- [ ] **Step 4: ExecutionLog**

`frontend/src/components/ExecutionLog.tsx`:

```tsx
import { Fragment, useState } from "react";
import { useApproveExecution } from "../api/hooks";
import type { ActivityOut } from "../api/types";
import { formatDay, formatHuf } from "../format";
import { Badge, statusBadge } from "./Badge";
import { Button } from "./Button";
import { ErrorMessage } from "./ErrorMessage";
import { Icon } from "./Icon";

function loggedAt(iso: string | null): string {
  return iso === null ? "Not run yet" : `${formatDay(iso)} ${iso.slice(11, 16)} UTC`;
}

function Audit({ row }: { row: ActivityOut }) {
  const items: [string, string][] = [
    ["Mandate", row.mandate_version === null ? "—" : `Version ${row.mandate_version}`],
    ["Clause", row.clause ?? "—"],
    ["Idempotency key", row.idempotency_key ?? "—"],
    ["Logged at", loggedAt(row.logged_at)],
  ];
  return (
    <dl className="grid gap-4 bg-surface-hover p-4 md:grid-cols-4">
      {items.map(([term, value]) => (
        <div key={term}>
          <dt className="text-caption text-text-muted">{term}</dt>
          <dd className="text-body font-semibold break-all">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

/**
 * Figma "Execution log table row" (3:210): Date, Event, Amount, Status, expandable audit row.
 * From 768 px a table; below it each row stacks (date and status on top, event, amount).
 */
export function ExecutionLog({ rows }: { rows: ActivityOut[] }) {
  const [open, setOpen] = useState<string | null>(null);
  const approve = useApproveExecution();
  if (rows.length === 0) return <p className="text-text-muted">Nothing has happened yet.</p>;
  return (
    <>
      <ErrorMessage error={approve.error} />
      <table className="w-full text-left text-body max-md:block">
        <thead className="text-caption text-text-muted max-md:hidden">
          <tr className="bg-surface-hover">
            <th className="px-3 py-2">Date</th>
            <th className="px-3 py-2">Event</th>
            <th className="px-3 py-2 text-right">Amount</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">
              <span className="sr-only">Details</span>
            </th>
          </tr>
        </thead>
        <tbody className="max-md:block">
          {rows.map((row) => {
            const badge = statusBadge(row.status);
            const expanded = open === row.key;
            return (
              <Fragment key={row.key}>
                <tr className="border-t border-border max-md:grid max-md:grid-cols-2 max-md:gap-1 max-md:py-3">
                  <td className="px-3 py-3 text-text-muted">{row.on}</td>
                  <td className="px-3 py-3 font-semibold max-md:order-3 max-md:col-span-2">{row.title}</td>
                  <td className="px-3 py-3 text-right max-md:order-4 max-md:text-left">
                    {row.amount === null ? "—" : formatHuf(row.amount)}
                  </td>
                  <td className="px-3 py-3 max-md:order-2 max-md:text-right">
                    <Badge tone={badge.tone}>{badge.label}</Badge>
                  </td>
                  <td className="px-3 py-1 max-md:order-5 max-md:col-span-2">
                    <div className="flex items-center justify-end gap-2">
                      {row.status === "awaiting_approval" && row.execution_id !== null ? (
                        <Button
                          aria-label={`Approve ${row.title}`}
                          disabled={approve.isPending}
                          onClick={() => {
                            if (row.execution_id !== null) approve.mutate(row.execution_id);
                          }}
                        >
                          Approve
                        </Button>
                      ) : null}
                      <button
                        type="button"
                        aria-label={`Audit details: ${row.title}`}
                        aria-expanded={expanded}
                        onClick={() => setOpen(expanded ? null : row.key)}
                        className="flex size-touch items-center justify-center rounded-md outline-none hover:bg-surface-hover focus-visible:shadow-focus"
                      >
                        <Icon name={expanded ? "chevron-down" : "chevron-right"} />
                      </button>
                    </div>
                  </td>
                </tr>
                {expanded ? (
                  <tr className="max-md:block">
                    <td colSpan={5} className="max-md:block">
                      <Audit row={row} />
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </>
  );
}
```

`max-md:` is Tailwind 4's built-in "below md" variant, not an arbitrary value. `iso.slice(11, 16)` shows the server's UTC time of day; it is formatting.

- [ ] **Step 5: Change amount modal, active plan and activity screens**

`frontend/src/screens/active-plan/ChangeAmountModal.tsx`:

```tsx
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

  const fieldError = revise.error instanceof ApiError && revise.error.field === "monthly_amount" ? revise.error.message : null;
  return (
    <Modal title="Change the monthly amount" onClose={onClose}>
      <form className="space-y-4" onSubmit={submit} noValidate>
        <p className="text-body">
          Your current plan keeps running until you sign the new amount. Signing pauses mandate version{" "}
          {plan.mandate_version} and signs a new version.
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
```

`frontend/src/screens/active-plan/ActivePlanScreen.tsx`:

```tsx
import { useState } from "react";
import { Link } from "react-router";
import { useActivePlan, useActivity, usePlanAction } from "../../api/hooks";
import type { PlanOut } from "../../api/types";
import { Badge } from "../../components/Badge";
import { Button, buttonClass } from "../../components/Button";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { ExecutionLog } from "../../components/ExecutionLog";
import { Modal } from "../../components/Modal";
import { StatTile } from "../../components/StatTile";
import { formatHuf } from "../../format";
import { ChangeAmountModal } from "./ChangeAmountModal";

function Orders({ plan }: { plan: PlanOut }) {
  return (
    <Card title="Recurring orders">
      <ul aria-label="Recurring orders" className="space-y-2">
        {plan.items.map((item) => (
          <li key={item.position} className="flex items-center gap-4 rounded-md border border-border px-4 py-2">
            <span aria-hidden="true" className="flex size-8 items-center justify-center rounded-full bg-primary text-caption text-on-primary">
              {item.position + 1}
            </span>
            <div className="flex-1">
              <p className="text-body font-semibold">{item.label}</p>
              <p className="text-caption text-text-muted">
                {item.product.name} · {item.due_on ? `until ${item.due_on}` : "monthly on the 1st"}
              </p>
            </div>
            <p className="text-body font-semibold">{formatHuf(item.monthly_amount)} / month</p>
          </li>
        ))}
      </ul>
    </Card>
  );
}

/** Figma 08 Active plan (8:708). */
export function ActivePlanScreen() {
  const plan = useActivePlan();
  const activity = useActivity();
  const pause = usePlanAction("pause");
  const [dialog, setDialog] = useState<"pause" | "amount" | null>(null);
  const data = plan.data;

  if (plan.error) return <ErrorMessage error={plan.error} />;
  if (data === undefined) return <p>Loading…</p>;
  if (data === null) {
    return (
      <div className="space-y-4">
        <h1 className="text-h1">Your savings plan</h1>
        <p className="text-text-muted">You have no savings plan yet.</p>
        <Link to="/questionnaire" className={buttonClass("primary")}>
          Start a savings plan
        </Link>
      </div>
    );
  }
  const active = data.status === "accepted";
  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-3 text-h1">
            Your savings plan <Badge tone={active ? "success" : "warning"}>{active ? "Active" : "Paused"}</Badge>
          </h1>
          <p className="text-text-muted">
            Accepted {data.signed_on} under mandate version {data.mandate_version}.
          </p>
        </div>
        {active ? (
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setDialog("amount")}>
              Change amount
            </Button>
            <Button variant="danger" onClick={() => setDialog("pause")}>
              Pause plan
            </Button>
          </div>
        ) : null}
      </header>
      {data.pending_revision !== null ? (
        <section className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-info bg-info-bg p-4 text-info">
          <p className="text-body">A new amount is waiting for your signature. Your current plan keeps running until then.</p>
          <Link to={`/plans/${data.pending_revision}`} className={buttonClass("secondary")}>
            Review the new amount
          </Link>
        </section>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Monthly amount" value={formatHuf(data.monthly_amount)} caption={`${data.items.length} recurring orders`} />
        <StatTile label="Next transfer" value={active ? data.next_transfer_on : "—"} caption="Checked against the mandate first" />
        <StatTile
          label="Saved by SaverAI"
          value={formatHuf(data.saved_total)}
          caption={data.saved_total === 0 ? "First transfer has not run yet" : "Executed transfers so far"}
        />
        <StatTile label="Mandate" value={`Version ${data.mandate_version ?? "—"}`} caption={`Signed ${data.signed_on ?? "—"}`} />
      </div>
      <Orders plan={data} />
      <Card title="Execution log">
        <p className="mb-4 text-body text-text-muted">
          Every transfer is checked against your mandate before it runs. Open a row for the audit details.
        </p>
        <ErrorMessage error={activity.error} />
        {activity.data ? <ExecutionLog rows={activity.data} /> : null}
      </Card>
      {dialog === "pause" ? (
        <Modal title="Pause your savings plan?" onClose={() => setDialog(null)}>
          <p className="text-body">No transfer runs while the mandate is paused (§4). You can start a new plan later.</p>
          <ErrorMessage error={pause.error} />
          <div className="mt-4 flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setDialog(null)}>
              Keep it running
            </Button>
            <Button
              variant="danger"
              disabled={pause.isPending}
              onClick={() => pause.mutate(data.id, { onSuccess: () => setDialog(null) })}
            >
              Pause plan
            </Button>
          </div>
        </Modal>
      ) : null}
      {dialog === "amount" ? <ChangeAmountModal plan={data} onClose={() => setDialog(null)} /> : null}
    </div>
  );
}
```

`data.items.length` counts the orders the API listed; `item.position + 1` is a display number.

`frontend/src/screens/activity/ActivityScreen.tsx`:

```tsx
import { useActivity } from "../../api/hooks";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { ExecutionLog } from "../../components/ExecutionLog";

/** Activity (sidebar): the execution log on its own page. */
export function ActivityScreen() {
  const activity = useActivity();
  return (
    <div className="space-y-6">
      <h1 className="text-h1">Activity</h1>
      <Card>
        <ErrorMessage error={activity.error} />
        {activity.data ? <ExecutionLog rows={activity.data} /> : <p>Loading…</p>}
      </Card>
    </div>
  );
}
```

In `frontend/src/App.tsx`, replace the `/plan` and `/activity` placeholders with `<ActivePlanScreen />` and `<ActivityScreen />`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass. In "pause asks for confirmation", two buttons are named "Pause plan" (header and dialog); the test scopes the second click to the dialog.

- [ ] **Step 7: Docs**

`docs/traceability.md`, AC6: append `; frontend/src/components/ExecutionLog.test.tsx::test_ac6_waiting_transfer_can_be_approved`.

`CHANGELOG.md`, `### Added`: `- Active plan (Figma 08) and Activity: stat tiles, recurring orders, execution log with audit details (mandate version, clause, idempotency key), transfer approval (AC6), pause with confirmation, change amount as a revision signed as the next mandate version (ADR-0004).`

Tick in `docs/tasks.md`: "Screens: login, home, questionnaire, plan review (with confidence level), time machine (chart with skipped months), mandate, active plan (pause)."

Run: `cd frontend && npm run fmt && npm run lint && cd .. && make docs-check`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): active plan and activity with execution log (AC6, AC7)`

---

### Task 18: Playwright e2e (desktop and 375 px), manual checks, docs, final verification

Deliverable: one Playwright run of the main workflow (questionnaire → analysis → plan → time machine → mandate → password → active plan) plus the AC5 path on a 1440 × 900 desktop viewport, 44 px target checks on every screen, a 375 px check that Home and Plan review have no horizontal scroll, updated docs, and a clean `make check` and `make e2e` from a fresh database.

**Files:**
- Create: `frontend/playwright.config.ts`, `frontend/e2e/global-setup.ts`, `frontend/e2e/main-flow.spec.ts`
- Modify: `docs/manual-checks.md`, `docs/architecture.md`, `docs/ai-usage.md`, `docs/traceability.md`, `README.md`, `CHANGELOG.md`, `docs/tasks.md`

**Interfaces:**
- Consumes: `make seed` personas (anna 6 months AC1 series, bence no surplus, csilla 2 months, dani 4 months; password `SEED_PASSWORD`), `manage.py flush|migrate|seed|run_orders`, every screen label from Tasks 9–17.
- Produces: `make e2e` green; titles `test_ac7_main_flow_questionnaire_plan_time_machine_mandate`, `test_ac5_customer_without_surplus_gets_explanation`, `layout has no horizontal scroll at 375 px`.

- [ ] **Step 1: Playwright config and database reset**

`frontend/playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  workers: 1, // one shared SQLite database
  use: {
    ...devices["Desktop Chrome"],
    viewport: { width: 1440, height: 900 }, // Figma desktop frames
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  // Reuses `make dev` servers when they run; starts them otherwise.
  webServer: [
    {
      command: "cd ../backend && uv run python manage.py runserver 8000",
      url: "http://localhost:8000/api/docs",
      reuseExistingServer: true,
    },
    { command: "npm run dev", url: "http://localhost:5173", reuseExistingServer: true },
  ],
});
```

`frontend/e2e/global-setup.ts`:

```ts
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const backend = fileURLToPath(new URL("../../backend", import.meta.url));

/**
 * Fresh demo data for every run: anna's plan from an earlier run would make signing a 409.
 * This WIPES the local development database.
 */
export default function globalSetup(): void {
  if (!process.env.SEED_PASSWORD) {
    throw new Error("SEED_PASSWORD is not set. Run `make e2e` (it loads .env).");
  }
  for (const args of [["migrate"], ["flush", "--no-input"], ["seed"]]) {
    execFileSync("uv", ["run", "python", "manage.py", ...args], { cwd: backend, stdio: "inherit" });
  }
}
```

- [ ] **Step 2: Write the e2e tests**

`frontend/e2e/main-flow.spec.ts`:

```ts
import { expect, test, type Page } from "@playwright/test";

const PASSWORD = process.env.SEED_PASSWORD ?? "";

async function login(page: Page, username: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("heading", { name: /^Hello, / })).toBeVisible();
}

/** AGENTS.md section 7: every visible interactive element is at least 44 px tall. */
async function expectTouchTargets(page: Page): Promise<void> {
  const targets = page.locator("button, a, input:not([type=radio]):not([type=checkbox]), label:has(input[type=radio]), label:has(input[type=checkbox])");
  for (const target of await targets.all()) {
    if (!(await target.isVisible())) continue;
    const box = await target.boundingBox();
    const name = await target.evaluate((element) => element.outerHTML.slice(0, 80));
    expect(box?.height ?? 0, name).toBeGreaterThanOrEqual(44);
  }
}

async function answerQuestionnaire(page: Page, fund: string): Promise<void> {
  await page.goto("/questionnaire");
  await page.getByLabel("Existing emergency fund").fill(fund);
  await page.getByRole("radio", { name: "3 Medium" }).check();
  await expectTouchTargets(page);
  await page.getByRole("button", { name: "Continue" }).click();
}

test("test_ac7_main_flow_questionnaire_plan_time_machine_mandate", async ({ page }) => {
  await login(page, "anna");
  await expectTouchTargets(page);

  await answerQuestionnaire(page, "0");
  await expect(page.getByRole("heading", { name: "Your spending analysis" })).toBeVisible();
  await expect(page.getByText("73,500 HUF").first()).toBeVisible(); // AC1
  await expectTouchTargets(page);

  await page.getByRole("link", { name: "See my plan" }).click();
  const panel = page.getByRole("complementary", { name: "Summary" });
  await expect(panel.getByText("73,500 HUF")).toBeVisible();
  await expect(page.getByRole("list", { name: "Plan items" }).getByRole("listitem").first()).toContainText("Emergency fund"); // AC2
  await expectTouchTargets(page);

  await page.getByRole("link", { name: "See month by month" }).click();
  await expect(page.getByRole("heading", { name: "Financial time machine" })).toBeVisible();
  await page.getByText("See month by month").click(); // open the table
  await expect(page.getByRole("table", { name: "Saved to date, month by month" })).toBeVisible(); // AC4
  await expectTouchTargets(page);

  await page.getByRole("link", { name: "Continue to mandate" }).click();
  await expect(page.getByRole("heading", { name: "Mandate · version 1" })).toBeVisible();
  await page.getByRole("checkbox", { name: "I have read the mandate and authorise these recurring orders." }).check();
  await expectTouchTargets(page);
  await page.getByRole("button", { name: "Sign mandate" }).click();

  const dialog = page.getByRole("dialog", { name: "Confirm with your password" });
  await dialog.getByLabel("Password").fill("not-the-password");
  await dialog.getByRole("button", { name: "Confirm and sign" }).click();
  await expect(dialog.getByRole("alert")).toHaveText("Incorrect password.");
  await dialog.getByLabel("Password").fill(PASSWORD);
  await dialog.getByRole("button", { name: "Confirm and sign" }).click();

  await expect(page.getByRole("heading", { name: /Your savings plan/ })).toBeVisible();
  await expect(page.getByText("Active", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Scheduled").first()).toBeVisible(); // next transfers in the log
  await expectTouchTargets(page);

  // AC7: the signed mandate offers no second signing.
  const planUrl = await page.evaluate(async () => {
    const response = await fetch("/api/plans/active");
    const plan = (await response.json()) as { id: number };
    return `/plans/${plan.id}/mandate`;
  });
  await page.goto(planUrl);
  await expect(page.getByText(/^Version 1, signed /)).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign mandate" })).toHaveCount(0);
});

test("test_ac5_customer_without_surplus_gets_explanation", async ({ page }) => {
  await login(page, "bence");
  await answerQuestionnaire(page, "0");
  await expect(page.getByRole("heading", { name: "No surplus to save right now" })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("no surplus");
  await expect(page.getByText("None")).toBeVisible(); // orders created
});

test("layout has no horizontal scroll at 375 px", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await login(page, "dani");
  const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(await overflow()).toBeLessThanOrEqual(0);
  await expect(page.getByRole("button", { name: "Open menu" })).toBeVisible();
  await answerQuestionnaire(page, "0");
  await page.getByRole("link", { name: "See my plan" }).click();
  await expect(page.getByRole("complementary", { name: "Summary" })).toBeVisible(); // bottom bar
  expect(await overflow()).toBeLessThanOrEqual(0);
});
```

The 375 px test uses dani (4 months, low confidence) so it does not depend on anna's state from the first test.

- [ ] **Step 3: Run e2e**

Run: `make e2e`
Expected: the setup prints migrations, flush and the seed summary, then `3 passed`. If a touch-target assertion fails, the message names the element's HTML: fix the component's classes (`min-h-touch`, `buttonClass`, `size-touch`), not the test. If an overflow assertion fails, find the wide element with Playwright's trace viewer (`npx playwright show-trace`) and fix its layout.

Run it again: `make e2e`. Expected: `3 passed` (the reset makes it repeatable).

- [ ] **Step 4: Manual checks**

Append to `docs/manual-checks.md`:

````markdown
## Frontend setup
`make setup && make migrate && make seed && make dev`, with `SAVERAI_FIXED_DATE=2026-10-08` in `.env`.
Open http://localhost:5173 in a desktop browser (1440 px wide).

## AC4 — time machine skipped months (UI)
1. Django admin (http://localhost:8000/admin/) → anna's account → balance 300000 → Save.
2. Log in as `anna` → Start a savings plan → fund 0, risk 3 → Continue → See my plan → See month by month.
Expected: skipped months are grey bars with a dashed amber outline and a warning marker; the
"Skipped months" card lists "…the transfer was skipped because it would have left less than
100,000 HUF on your account."; "Months skipped" shows their count.

## AC6 — approving a transfer (UI)
1. Log in as `dani` → Start a savings plan → fund 0, risk 3 → Continue → See my plan.
Expected: "Low confidence" badge and "Every transfer needs your approval".
2. Continue to mandate → tick the consent → Sign mandate → password → Confirm and sign.
3. Terminal: `cd backend && uv run python manage.py run_orders`.
4. Reload "Savings plan".
Expected: the log row shows "Needs approval"; its audit details show "§3 · This transfer needs your
approval." Press "Approve". Expected: the row changes to "Done".

## Change amount → mandate version 2 (UI)
1. As anna with an active plan: Savings plan → Change amount → 50000 → Propose new amount.
Expected: plan review of the new amount; the old plan still shows "Active" until signing.
2. Continue to mandate. Expected: "Mandate · version 2". Sign with the password.
Expected: Savings plan shows mandate version 2; the log keeps "signed mandate version 1" and adds
"Plan paused: mandate version 1 stopped (§4)".

## Keyboard, focus and screen reader basics
1. On every screen, press Tab through all controls.
Expected: every control shows the 2 px white + 2 px blue focus ring; order follows the screen.
2. Questionnaire: ← → change the risk score; Enter submits. Password modal: focus stays inside,
Esc closes, Enter confirms.
3. VoiceOver (Cmd+F5): every button and field announces a name.

## Responsive (768–1023 px and 375 px)
1. Resize to 900 px. Expected: the sidebar becomes a top bar with "Open menu"; the menu opens a
drawer; Esc closes it. Plan review and Mandate stack; the summary panel is a bottom bar.
2. Resize to 375 px. Expected: one column, no horizontal scrolling; the execution log shows stacked
rows (date and status on top, event, amount).

## RuleConfig change in the UI (defence rehearsal, AC1)
1. Django admin → Rule configuration → "Monthly share percent" = 60 → Save.
2. Log in as `anna` → Start a savings plan → fund 0, risk 3 → Continue.
Expected: suggested amount 63,000 HUF, "60% of the median"; Home's rule card says 60%. Set it back to 70.
````

- [ ] **Step 5: Architecture, README, traceability**

Append to `docs/architecture.md`:

````markdown
## Frontend
React SPA in `frontend/` (ADR-0003), built from the Figma file (UI design section above). Screens in
`src/screens/<name>/`, shared UI in `src/components/`, tokens from the Figma variables in
`src/theme/theme.css`.

```
screen → hook (src/api/hooks.ts, TanStack Query) → apiFetch (src/api/client.ts) → /api (Vite proxy) → Django Ninja
```

- The frontend computes no money, date or rule decision; it formats API values (`src/format.ts`) and
  renders backend texts verbatim. "Today" is `GET /api/account` → `today`.
- Auth: Django session cookie; `apiFetch` sends `X-CSRFToken` from the cookie on every unsafe request.
  Any 401 clears the cached user and the router sends the customer to `/login`. Signing a mandate
  asks for the password again (ADR-0004).
- Routes: `/login`; sidebar layout: `/`, `/plan`, `/activity`; plan flow: `/questionnaire` (incl. no
  surplus and too little data), `/plans/:planId/analysis`, `/plans/:planId`,
  `/plans/:planId/time-machine`, `/plans/:planId/mandate`.
````

Add to `README.md`:

```markdown
## Using the app
After `make seed` and `make dev`, open http://localhost:5173 and log in as a demo persona
(password: `SEED_PASSWORD` from `.env`). Signing a mandate asks for the same password.
Admin users use Django admin at http://localhost:8000/admin/. UI design: Figma file
https://www.figma.com/design/QUT5rnXj1U6BYjty7YH5uS.
```

In `docs/traceability.md`, append to the evidence cells:
- AC1: `; frontend/e2e/main-flow.spec.ts::test_ac7_main_flow_questionnaire_plan_time_machine_mandate`
- AC5: `; frontend/e2e/main-flow.spec.ts::test_ac5_customer_without_surplus_gets_explanation`
- AC7: `; frontend/e2e/main-flow.spec.ts::test_ac7_main_flow_questionnaire_plan_time_machine_mandate`
- AC4 and AC6: change Verification to `automated + manual` and append `; manual steps in docs/manual-checks.md#ac4--time-machine-skipped-months-ui` (AC4) and `; manual steps in docs/manual-checks.md#ac6--approving-a-transfer-ui` (AC6).

- [ ] **Step 6: Draft the AI usage entry**

Append to `docs/ai-usage.md` (the human author verifies and completes the decision fields):

```markdown
### Case 5 — Frontend test strategy from the Figma design (DRAFT, author to complete)
- Phase: testing
- Tool and model: Claude Code, Claude Opus 5.5 (superpowers "writing-plans" skill, Figma MCP server)
- Problem: test a React UI whose every value comes from the backend, so that tests are fast and
  deterministic and still prove AC1–AC8 from the customer's side, including the Figma layouts.
- Context given and key instruction: `docs/specification.md`, `AGENTS.md`, `docs/tasks.md`, the Figma
  file QUT5rnXj1U6BYjty7YH5uS (frames, variables, responsive notes); "check whether the Figma design
  is present and do another frontend implementation plan with the superpowers skill".
- Essence of the AI suggestion: Vitest + Testing Library with a small `fetch` stub instead of MSW;
  AC tests named `test_acN_...` and checked by `make docs-check`; AC4 asserted on the month table, not
  the chart SVG (jsdom has no layout); a token guard test that forbids hex colours, arbitrary values
  and client clock reads; one Playwright main flow on 1440 px with 44 px target checks and a wrong
  password attempt, plus a 375 px no-horizontal-scroll check; backend fields added so the UI never
  computes amounts, dates or progress.
- Decision (accepted / modified / rejected) and technical reasons: TODO author
- Verification: `make check` (Vitest), `make e2e` (Playwright), `docs/traceability.md`.
- Limitations of this verification: component tests stub the API, so contract drift between
  `src/api/types.ts` and `backend/api/schemas.py` is caught only by the e2e test. jsdom cannot check
  layout or colour contrast; the 375 px e2e and the manual checks cover those.
```

- [ ] **Step 7: Changelog and tasks**

`CHANGELOG.md`, `### Added`:

```markdown
- Playwright e2e of the main workflow (questionnaire → analysis → plan → time machine → mandate with password → active plan), the no-surplus path, 44 px target checks and a 375 px no-horizontal-scroll check (AC1, AC2, AC4, AC5, AC7).
- Frontend manual checks, architecture section and AI usage Case 5 draft (testing phase).
```

Tick in `docs/tasks.md`: the `Makefile` item, "One Playwright e2e of the main workflow …", "`README.md`: setup, run, test commands, link to `docs/ai-usage.md`.", "`docs/manual-checks.md`: reproducible steps for UI-only checks." Leave "AI usage Case 2 … and Case 3 …" and the tag for the author: Case 5 (testing) is the draft that covers the testing phase; the author decides whether it replaces the "Case 3 (testing phase)" item.

- [ ] **Step 8: Final verification from a clean state**

Run:

```bash
rm -rf frontend/node_modules
make setup
make check
make e2e
cd frontend && npm run build
```

Expected: `make check` — backend lint and tests green, `tsc` / ESLint / Prettier clean, all Vitest tests pass, `docs-check: OK`; `make e2e` — `3 passed`; Vite build succeeds.

In `docs/traceability.md`, update the "Last full run" line with the date and the backend, Vitest and Playwright counts from this output.

- [ ] **Step 9: Suggested commit (user commits)**

`test(e2e): main workflow and responsive checks, manual checks and frontend docs`

After the user commits: tagging `v1.0-first-version` is the author's step and out of scope.
