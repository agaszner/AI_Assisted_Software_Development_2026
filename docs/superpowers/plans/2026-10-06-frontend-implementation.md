# SaverAI Frontend (M2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Commits:** the user asked for **no commits**. Every task ends with a *suggested* Conventional Commit message; the user runs `git commit` themselves. Do not run `git commit`, `git tag` or `git push`. If the user later says to commit, replace each "Suggested commit" step with a real commit.

**Goal:** Build the M2 frontend of SaverAI: a mobile banking UI in React with login, home, questionnaire, plan review (with confidence level), time machine (chart with skipped months), mandate and active plan (pause, transfer approval), plus the explanation states for no surplus (AC5) and too little data (AC6). Add one Playwright e2e test of the main workflow.

**Architecture:** `frontend/` is a Vite + React + TypeScript (strict) single-page app. It talks only to the Django Ninja API from the backend plan, through one fetch wrapper (`src/api/client.ts`) and TanStack Query hooks (`src/api/hooks.ts`). The Vite dev server proxies `/api` to `localhost:8000`, so the session and CSRF cookies are same-origin. The frontend **computes nothing**: every amount, product, confidence level, explanation and skipped-month note comes from the API; the frontend only formats and parses. One small backend task adds the two read endpoints the screens need (account, mandate).

**Tech Stack:** Node 22, npm, Vite 8, React 19, TypeScript 6.0 (strict), React Router 8, TanStack Query 5, Recharts 3, Tailwind CSS 4 (`@tailwindcss/vite`, tokens in `@theme`), Vitest 5 + jsdom + Testing Library, Playwright 1.63, ESLint 10 + typescript-eslint, Prettier 3.

**Spec:** `docs/specification.md` (AC1–AC8). Also read `AGENTS.md` (golden rules, layout, documentation rules), `docs/tasks.md` (M2 frontend list) and the backend plan `docs/superpowers/plans/2026-10-06-backend-implementation.md` (Task 13 defines the API contract this plan consumes). If code and spec disagree, the spec wins: stop and flag it.

## Prerequisites and order

- **Task 1 needs backend plan Tasks 1–2 done**: it edits `scripts/docs_check.py`, makes `make check` depend on `docs-check`, and runs `make docs-check`. The traceability steps of Tasks 7–11 also need `docs/traceability.md` from backend Task 2.
- **Task 2 (backend endpoints) needs backend plan Tasks 1–13 done.** Task 12 (e2e) needs the whole backend plan done (`make seed`, `run_orders`).
- The screen code and tests of Tasks 3–11 use a stubbed `fetch`, so they need only the API contract, not a running backend. Run the tasks in order: they append to shared files (`src/api/hooks.ts`, routes in `src/App.tsx`).
- Run every command from the repository root unless a step says `cd frontend` or `cd backend`.

## Global Constraints

- No AI at runtime: no LLM SDK, model call or AI dependency in `frontend/`.
- The frontend computes no money and makes no rule decision. Amounts, products, confidence, explanations and skipped-month notes come from the API. The frontend only formats values (`formatHuf`) and parses customer input (`parseHuf`).
- Money is a whole number of forints (`Huf = number`, always an integer). Inputs are parsed with `parseHuf`. Never send a float or a numeric string; the backend answers 422 for `100.0`, `"100"`, `true`.
- Explanation texts (`explanations[]`, the time machine `note`, error `detail`) are rendered exactly as the backend sends them. Do not write client-side templates for rule results.
- No `new Date()` / `Date.now()` for business decisions. The past-date check belongs to the server (it honours `SAVERAI_FIXED_DATE`). Dates are shown by slicing ISO strings (`formatMonth`, `formatDay`), so there is no time-zone shift.
- TypeScript `strict`, no `any` (ESLint `@typescript-eslint/no-explicit-any: error`), no non-null assertions.
- Colours, spacing and radii only from tokens in `src/theme/theme.css`. Tailwind's default palette is disabled (`--color-*: initial`), so `bg-gray-100` does not exist. No hex colours and no arbitrary values (`p-[13px]`) in components (enforced by `src/theme/tokens.test.ts`).
- Every interactive element has a 44 px minimum touch target (`min-h-touch`) and an accessible name (visible label text or `aria-label`). Links use `buttonClass()` so they get the same target. Playwright checks the heights (Task 12).
- Dev server port is **5173** (`strictPort`), because the backend's `CSRF_TRUSTED_ORIGINS` is `http://localhost:5173`.
- AC test names: `test_acN_<behaviour>` as the Vitest / Playwright test title (e.g. `test("test_ac5_no_surplus_shows_explanation_without_plan", …)`), so `make docs-check` can find them.
- No dependency beyond ADR-0003 (Task 1). Never edit or delete a failing test to make it pass.
- Every task updates `CHANGELOG.md` (`## [Unreleased]`) and, if it adds an AC test, `docs/traceability.md` in the same change (AGENTS.md section 8).

## Review Focus

Spec-silent inputs most likely to hurt a real user. Each has a pinned test in the owning task.

1. **CSRF token rotation after login.** Django rotates the CSRF token on login. A token cached before login gives 403 on the first POST after login → the client reads the `csrftoken` cookie on every unsafe request (Task 3: `test("uses the current csrftoken cookie on every unsafe request")`).
2. **Amount typed as a decimal, with a sign, as text or empty** (`100.5`, `-5`, `1e5`, `abc`, `""`) → a field error and no request; `250 000` and `250,000` are accepted as 250000 (Task 4: `parseHuf` tests; Task 7: `test("rejects a decimal amount without calling the API")`).
3. **Session expires mid-flow** (any API call answers 401) → the customer lands on the login screen, not on an error page (Task 6: `test("an expired session mid-flow returns to login")`).
4. **Double tap on Accept, or Accept while another plan is active** → exactly one request; the 409 message is shown and nothing navigates (Task 10: `test_ac7_accept_button_is_disabled_while_accepting`, `test("shows the conflict message when another plan is active")`).
5. **No active plan** (`GET /api/plans/active` → 404) → an empty state with a "Start a savings plan" link, not an error (Task 6: `test("shows a start link when there is no active plan")`; Task 11: `test("shows the empty state when there is no active plan")`).

## Interpretations, deviations and deferrals

Recorded in ADR-0003 (Task 1) and this plan. The user approves them by approving this plan.

- **Two backend endpoints are added** (Task 2, no data model change): `GET /api/account` (balance and the 10 newest transactions up to today, for Home and `TransactionRow`) and `GET /api/plans/{id}/mandate` (terms, clauses, minimum balance, products; `version` is null while the plan is only proposed). Without them the frontend would have to hard-code 100,000 HUF and the clause texts, which breaks golden rule 2 and the `RuleConfig` rule.
- **Mandate screen = signing.** The backend signs mandate version N+1 when a plan is accepted. The mandate screen shows the terms that will be signed; the "Sign mandate and accept plan" button calls `POST /api/plans/{id}/accept`.
- **Seven screens** (login, home, questionnaire, plan review, time machine, mandate, active plan). AGENTS.md mentions "Figma 01–10", but no Figma file is in the repository. Tokens are hand-written in `src/theme/theme.css`; swap the values for Figma variables when a file exists.
- **`GET /api/analysis` is not used.** The plan explanations already state the median surplus and the 70 % share. Add an analysis view only if the defence needs it.
- **No client-side past-date check** (it would disagree with `SAVERAI_FIXED_DATE`); the server's 422 message is shown.
- **No "resume paused plan"**: the spec only requires pausing.
- **React Router is added** (not in AGENTS.md section 3): each screen gets a URL, so the back button, reload and Playwright deep links work. Recorded in ADR-0003; AGENTS.md section 3 is updated.
- **No MSW**: tests stub `fetch` with `vi.stubGlobal` (`src/test/render.tsx`).
- **`make e2e` resets the local database** (flush, migrate, seed) so the main flow can run repeatedly. Otherwise anna's earlier accepted plan would make the second run fail with 409.
- **Admin role** keeps using Django admin at `http://localhost:8000/admin/`; the React app is the customer UI.
- **`make docs-check` learns frontend references** (`frontend/…test.tsx::name`, `frontend/e2e/…spec.ts::name`): the file must exist and contain the quoted test title.

## File map

```
Makefile                                         Task 1
README.md                                        Task 1, 2, 12
AGENTS.md (sections 3, 4)                        Task 1
CHANGELOG.md                                     every task
scripts/docs_check.py                            Task 1
docs/decisions/0003-frontend-stack.md            Task 1
docs/traceability.md                             Task 2, 7–12
docs/architecture.md (Frontend section)          Task 12
docs/manual-checks.md                            Task 12
docs/ai-usage.md                                 Task 12 (draft entry)
backend/api/schemas.py, backend/api/routes.py    Task 2
backend/tests/api/test_account_mandate_api.py    Task 2
frontend/package.json, package-lock.json         Task 1
frontend/index.html, tsconfig.json, vite.config.ts, eslint.config.js,
  .prettierrc.json, .prettierignore              Task 1
frontend/playwright.config.ts                    Task 12
frontend/src/main.tsx                            Task 1, 5
frontend/src/App.tsx, App.test.tsx               Task 1, 5, then one route per screen task
frontend/src/test/setup.ts                       Task 1, 3
frontend/src/test/render.tsx                     Task 3 (mockApi, renderScreen), Task 5 (renderApp)
frontend/src/test/fixtures.ts                    Task 3
frontend/src/api/types.ts                        Task 3   mirrors backend/api/schemas.py
frontend/src/api/client.ts                       Task 3   apiFetch, ApiError, CSRF
frontend/src/api/queryClient.ts                  Task 3   makeQueryClient
frontend/src/api/hooks.ts                        Task 5, then each screen task appends its hooks
frontend/src/format.ts                           Task 4   formatHuf, formatMonth, formatDay, parseHuf
frontend/src/theme/theme.css, tokens.test.ts     Task 1 (import only), Task 4
frontend/src/components/{Button,TextField,ErrorMessage,TabBar,Screen,TransactionRow}.tsx   Task 4
frontend/src/components/PlanItemList.tsx         Task 8
frontend/src/screens/login/LoginScreen.tsx               Task 5
frontend/src/screens/home/HomeScreen.tsx                 Task 6
frontend/src/screens/questionnaire/QuestionnaireScreen.tsx   Task 7   AC5, AC6, AC8
frontend/src/screens/plan-review/PlanReviewScreen.tsx    Task 8   AC6, AC7, AC8
frontend/src/screens/time-machine/TimeMachineScreen.tsx  Task 9   AC4
frontend/src/screens/mandate/MandateScreen.tsx           Task 10  AC7
frontend/src/screens/active-plan/ActivePlanScreen.tsx    Task 11  AC6
frontend/e2e/global-setup.ts, main-flow.spec.ts          Task 12  AC1, AC5, AC7
```

Every screen has a `*.test.tsx` next to it.

---

### Task 1: Frontend skeleton, tooling, Makefile, ADR-0003, docs-check for frontend tests

Deliverable: `make lint`, `make test-fe` and `make docs-check` are green on a Vite + React skeleton. This task verifies the toolchain versions that later tasks rely on.

**Files:**
- Create: `frontend/package.json`, `frontend/index.html`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/eslint.config.js`, `frontend/.prettierrc.json`, `frontend/.prettierignore`
- Create: `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `frontend/src/test/setup.ts`, `frontend/src/theme/theme.css`
- Create: `docs/decisions/0003-frontend-stack.md`
- Modify: `Makefile`, `scripts/docs_check.py`, `README.md`, `AGENTS.md` (sections 3 and 4), `CHANGELOG.md`

**Interfaces:**
- Consumes: `scripts/docs_check.py` and `Makefile` from backend plan Tasks 1–2.
- Produces: npm scripts `dev`, `build`, `test`, `lint`, `fmt`, `e2e`; Make targets `dev-backend`, `dev-frontend`, `test-fe`, `e2e`; `App` component exported from `src/App.tsx`; Vitest setup file `src/test/setup.ts`.

- [ ] **Step 1: Write ADR-0003 (dependency approval record)**

Create `docs/decisions/0003-frontend-stack.md`:

```markdown
# 0003. Frontend tech stack and dependencies
Date: 2026-10-06 · Status: proposed

## Context
AGENTS.md section 3 fixes React + TypeScript (strict) + Vite, Tailwind CSS, TanStack Query and
Recharts. ADR-0001 deferred the frontend dependencies to the frontend plan. This ADR lists every
frontend dependency so none is added silently.

## Decision
- Node 22 or newer, **npm** with a committed `frontend/package-lock.json`.
- Runtime: **react** and **react-dom** 19, **react-router** 8 (one URL per screen: back button,
  reload and Playwright deep links work), **@tanstack/react-query** 5 (server state, cache
  invalidation after accept / pause), **recharts** 3 (time machine chart).
- Build: **vite** 8, **@vitejs/plugin-react**, **typescript ~6.0** (typescript-eslint supports
  TypeScript < 6.1, so TypeScript 7 is not used yet), **tailwindcss** 4 with **@tailwindcss/vite**
  (design tokens in `src/theme/theme.css` `@theme`; the default palette is disabled).
- Tests: **vitest** 5, **jsdom**, **@testing-library/react**, **@testing-library/user-event**,
  **@testing-library/jest-dom**, **@playwright/test** (Chromium only).
- Quality: **eslint** 10, **@eslint/js**, **typescript-eslint**, **eslint-plugin-react-hooks**,
  **globals**, **prettier**; types **@types/react**, **@types/react-dom**, **@types/node**.
- No AI / LLM dependency (AGENTS.md golden rule 1).
- Not added: MSW (tests stub `fetch`), axios (`fetch` is enough), form libraries, date libraries
  (ISO date strings are sliced), global state libraries (TanStack Query holds server state).

## Alternatives considered
- A `useState` screen switch instead of a router: no deep links, no back button, harder e2e.
- MSW for API mocks: one more dependency for what a 25-line `fetch` stub does.
- Tailwind 3 with `tailwind.config.js`: Tailwind 4 keeps the tokens in CSS, one file.
- TypeScript 7: not yet supported by typescript-eslint.

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

`frontend/src/theme/theme.css` (Task 4 adds the tokens):

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
/** Placeholder; Task 5 replaces it with the router. */
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

If the backend `Makefile` has no `seed` target yet (backend plan Task 10 adds it), drop `seed` from `.PHONY` for now.

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

Temporarily append `; frontend/src/App.test.tsx::test_ac1_missing` to the AC1 evidence cell in `docs/traceability.md` (AC1 is `passing` once the backend plan is done; if it is still `planned`, set it to `passing` temporarily too). Run `make docs-check`.
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

- [ ] **Step 11: Full check**

Run: `make fmt && make check`
Expected: backend lint and tests unchanged and green, `1 passed` from Vitest, `docs-check: OK`.

- [ ] **Step 12: Suggested commit (user commits)**

`feat(frontend): vite react typescript skeleton and tooling (ADR-0003)`

---

### Task 2: Backend read endpoints for the home and mandate screens

Deliverable: `GET /api/account` and `GET /api/plans/{id}/mandate`, with ownership checks. No data model change.

**Files:**
- Modify: `backend/api/schemas.py`, `backend/api/routes.py`
- Create: `backend/tests/api/test_account_mandate_api.py`
- Modify: `docs/traceability.md` (AC8 row), `README.md` (API paragraph), `CHANGELOG.md`

**Interfaces:**
- Consumes (backend plan): `current_user` (Task 1), `get_clock` (Task 3), `Account`, `Transaction`, `Product` (Task 9), `Mandate`, `RuleConfig`, `Plan.per_transfer_approval` (Task 9), `rules.mandate.CLAUSES` (Task 8), `services.get_owned_plan` via `owned_plan`, `plan_out` (Task 13), `create_catalogue`, `create_customer` (Task 10), `AC1_SERIES`, `TODAY` (Task 3)
- Produces:

| Method | Path | Response |
| --- | --- | --- |
| GET | `/api/account` | `AccountOut {name, balance, transactions: TransactionOut[]}`; 404 when the user has no account |
| GET | `/api/plans/{id}/mandate` | `MandateOut {status: "unsigned"\|"active"\|"paused", version: int\|null, signed_at: datetime\|null, max_monthly_amount, min_balance, per_transfer_approval, products: ProductOut[], clauses: ClauseOut[]}`; 403 another customer's plan |

`TransactionOut {id, booked_on, amount, description}`, `ClauseOut {number, text}`. Also `api.routes.product_out(product: Product) -> ProductOut`.

- [ ] **Step 1: Write the failing tests**

`backend/tests/api/test_account_mandate_api.py`:

```python
from datetime import timedelta
from typing import Any

import pytest
from django.contrib.auth.models import User
from django.test import Client

from banking.models import Account, Product, Transaction
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


def test_account_shows_balance_and_ten_newest_transactions(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES, balance=600_000))
    body = client.get("/api/account").json()
    assert body["balance"] == 600_000
    dates = [t["booked_on"] for t in body["transactions"]]
    assert len(dates) == 10
    assert dates == sorted(dates, reverse=True)


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
    assert (preview["status"], preview["version"], preview["signed_at"]) == ("unsigned", None, None)
    assert (preview["max_monthly_amount"], preview["min_balance"]) == (73_500, 100_000)
    assert [c["number"] for c in preview["clauses"]] == sorted(CLAUSES)
    assert preview["products"]

    assert post(client, f"/api/plans/{plan_id}/accept").status_code == 200
    signed = client.get(f"/api/plans/{plan_id}/mandate").json()
    assert (signed["status"], signed["version"]) == ("active", 1)
    assert signed["signed_at"] is not None
    for key in ("max_monthly_amount", "min_balance", "per_transfer_approval", "products", "clauses"):
        assert signed[key] == preview[key], key


def test_ac8_other_customer_cannot_view_mandate(client: Client) -> None:
    client.force_login(create_customer("anna", AC1_SERIES))
    plan_id = proposed_plan_id(client)
    client.logout()
    client.force_login(create_customer("bob", AC1_SERIES))
    assert client.get(f"/api/plans/{plan_id}/mandate").status_code == 403
```

`test_mandate_preview_matches_signed_mandate` pins the one risk of this task: the preview is built in the route, the signed mandate in `services.accept_plan`. If someone changes one side, this test fails.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/api/test_account_mandate_api.py`
Expected: FAIL — `/api/account` and `/api/plans/{id}/mandate` return 404 (routes do not exist).

- [ ] **Step 3: Add the schemas**

In `backend/api/schemas.py`, change the date import to `from datetime import date, datetime` and append:

```python
class TransactionOut(Schema):
    id: int
    booked_on: date
    amount: int
    description: str


class AccountOut(Schema):
    name: str
    balance: int
    transactions: list[TransactionOut]


class ClauseOut(Schema):
    number: int
    text: str


class MandateOut(Schema):
    status: str  # "unsigned" (plan only proposed), "active" or "paused"
    version: int | None
    signed_at: datetime | None
    max_monthly_amount: int
    min_balance: int
    per_transfer_approval: bool
    products: list[ProductOut]
    clauses: list[ClauseOut]
```

- [ ] **Step 4: Add the routes**

In `backend/api/routes.py`:

1. Add the imports (`make fmt` sorts them): `from banking.models import Account, Product` and `from rules.mandate import CLAUSES`; add `Mandate` to the existing `from plans.models import ...` line (it already imports `RuleConfig`); add `AccountOut`, `ClauseOut`, `MandateOut`, `TransactionOut` to the `api.schemas` import list.

2. Add a module constant below `router = Router(...)`:

```python
# Display limit for the home screen, not a rule parameter.
RECENT_TRANSACTIONS = 10
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
    rows = account.transactions.filter(booked_on__lte=get_clock().today()).order_by(
        "-booked_on", "-id"
    )[:RECENT_TRANSACTIONS]
    return AccountOut(
        name=account.name,
        balance=account.balance,
        transactions=[
            TransactionOut(
                id=t.pk, booked_on=t.booked_on, amount=t.amount, description=t.description
            )
            for t in rows
        ],
    )


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
    return MandateOut(
        status="unsigned",
        version=None,
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

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/api -v`
Expected: all pass, including the 6 new tests and the unchanged `test_plans_api.py`.

- [ ] **Step 6: Docs and check**

In `docs/traceability.md`, append to the AC8 evidence cell: `; tests/api/test_account_mandate_api.py::test_ac8_other_customer_cannot_view_mandate`.

In `README.md`, extend the API paragraph's endpoint list with: `account (balance, recent transactions), plan mandate (terms and clauses)`.

Add to `CHANGELOG.md` under `### Added`:

```markdown
- API: `GET /api/account` (balance, 10 newest transactions) and `GET /api/plans/{id}/mandate` (mandate terms and clauses, preview before acceptance); another customer's mandate returns 403 (AC8).
```

Run: `make fmt && make check`. Expected: green.

- [ ] **Step 7: Suggested commit (user commits)**

`feat(api): account and mandate read endpoints for the frontend (AC8)`

---

### Task 3: API types, fetch client with CSRF, query client, test helpers

Deliverable: a typed `apiFetch` that sends the current CSRF token, turns error bodies into readable messages, and test helpers that stub the API.

**Files:**
- Create: `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/api/client.test.ts`, `frontend/src/api/queryClient.ts`
- Create: `frontend/src/test/render.tsx`, `frontend/src/test/fixtures.ts`
- Modify: `frontend/src/test/setup.ts`, `CHANGELOG.md`

**Interfaces:**
- Consumes: the API contract of backend plan Task 13 and Task 2 above.
- Produces:
  - `types.ts`: `Huf`, `Role`, `Me`, `LoginIn`, `ExpenseIn`, `QuestionnaireIn`, `IdOut`, `Confidence`, `PlanStatus`, `Outcome`, `ProductOut`, `PlanItemOut`, `PlanOut`, `ProposalOut`, `BacktestMonthOut`, `TimeMachineOut`, `ExecutionStatus`, `ExecutionOut`, `TransactionOut`, `AccountOut`, `ClauseOut`, `MandateStatus`, `MandateOut`
  - `client.ts`: `class ApiError extends Error { status: number }`, `apiFetch<T>(path: string, options?: { method?: "GET" | "POST" | "PATCH"; body?: unknown }): Promise<T>`
  - `queryClient.ts`: `makeQueryClient(onUnauthorized?: () => void): QueryClient`
  - `render.tsx`: `mockApi(routes: Record<string, Handler>): Call[]`, `renderScreen(element, { path?, url? }): QueryClient`, types `Reply`, `Handler`, `Call`
  - `fixtures.ts`: `PLAN: PlanOut`, `plan(overrides?: Partial<PlanOut>): PlanOut`

- [ ] **Step 1: Write the API types (mirror of `backend/api/schemas.py`)**

`frontend/src/api/types.ts`:

```ts
/**
 * Mirror of backend/api/schemas.py. Keep field names and enum values identical.
 * Dates are ISO strings ("2026-09-01"); datetimes are ISO strings with time.
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

export interface ProductOut {
  id: number;
  name: string;
  risk_level: number;
  liquid: boolean;
}

export interface PlanItemOut {
  kind: "emergency_fund" | "planned_expense" | "investment";
  label: string;
  product: ProductOut;
  monthly_amount: Huf;
  target_amount: Huf | null;
}

export interface PlanOut {
  id: number;
  status: PlanStatus;
  monthly_amount: Huf;
  proposed_amount: Huf;
  confidence: Confidence;
  per_transfer_approval: boolean;
  items: PlanItemOut[];
  explanations: string[];
}

export interface ProposalOut {
  outcome: Outcome;
  plan: PlanOut | null;
  explanations: string[];
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

export interface TransactionOut {
  id: number;
  booked_on: string;
  amount: Huf;
  description: string;
}

export interface AccountOut {
  name: string;
  balance: Huf;
  transactions: TransactionOut[];
}

export interface ClauseOut {
  number: number;
  text: string;
}

export type MandateStatus = "unsigned" | "active" | "paused";

export interface MandateOut {
  status: MandateStatus;
  version: number | null;
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
import type { PlanOut } from "../api/types";

/** A proposed plan matching AC1 (73,500 HUF from a 105,000 HUF median). */
export const PLAN: PlanOut = {
  id: 7,
  status: "proposed",
  monthly_amount: 73_500,
  proposed_amount: 73_500,
  confidence: "normal",
  per_transfer_approval: false,
  items: [
    {
      kind: "investment",
      label: "Long-term investment",
      product: { id: 4, name: "Balanced fund", risk_level: 3, liquid: false },
      monthly_amount: 73_500,
      target_amount: null,
    },
  ],
  explanations: [
    "We suggest saving 73,500 HUF a month: 70% of your median monthly surplus of 105,000 HUF.",
  ],
};

export function plan(overrides: Partial<PlanOut> = {}): PlanOut {
  return { ...PLAN, ...overrides };
}
```

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

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
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
  if (!response.ok) throw new ApiError(response.status, messageFrom(data, response.status));
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
Expected: all pass (8 client tests + 1 app test).

- [ ] **Step 7: Lint, changelog**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend API client: typed mirror of the API schemas, CSRF token read on every request, readable messages for 403 / 409 / 422 errors.
```

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): typed api client with csrf handling and test helpers`

---

### Task 4: Theme tokens, formatting and shared components

Deliverable: design tokens, money / date formatting and parsing, and the shared components every screen uses: `Button`, `TextField`, `ErrorMessage`, `TabBar`, `Screen`, `TransactionRow`.

**Files:**
- Modify: `frontend/src/theme/theme.css`
- Create: `frontend/src/theme/tokens.test.ts`, `frontend/src/format.ts`, `frontend/src/format.test.ts`
- Create: `frontend/src/components/Button.tsx`, `TextField.tsx`, `ErrorMessage.tsx`, `TabBar.tsx`, `Screen.tsx`, `TransactionRow.tsx`, `components.test.tsx`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `Huf`, `TransactionOut` (Task 3).
- Produces:
  - `format.ts`: `formatHuf(amount: Huf): string` (`73500` → `"73,500 HUF"`), `formatMonth(iso: string): string` (`"2026-09-01"` → `"2026-09"`), `formatDay(iso: string): string` (first 10 chars), `parseHuf(text: string): Huf | null`, `AMOUNT_HINT: string`
  - `Button({ variant?: "primary" | "secondary" | "danger", ...buttonProps })`, `buttonClass(variant?): string` (for `Link`s)
  - `TextField({ label: string, ...inputProps })`
  - `ErrorMessage({ error: unknown })` — renders `role="alert"` for an `Error` or a string, nothing for null
  - `TabBar()` — links Home `/`, New plan `/questionnaire`, My plan `/active`
  - `Screen({ title: string, children })` — `<h1>{title}</h1>`, content, `TabBar`
  - `TransactionRow({ transaction: TransactionOut })` — `<li>`
  - Tailwind token utilities: colours `canvas surface ink muted line brand on-brand positive danger warning`; spacing `touch` (44px); radius `card`.

- [ ] **Step 1: Write the failing tests**

`frontend/src/format.test.ts`:

```ts
import { describe, expect, test } from "vitest";
import { formatDay, formatHuf, formatMonth, parseHuf } from "./format";

test("formatHuf matches the backend explanation format", () => {
  expect(formatHuf(73_500)).toBe("73,500 HUF");
  expect(formatHuf(-40_000)).toBe("-40,000 HUF");
  expect(formatHuf(0)).toBe("0 HUF");
});

test("dates are sliced, never shifted by time zone", () => {
  expect(formatMonth("2026-09-01")).toBe("2026-09");
  expect(formatDay("2026-10-06T23:30:00Z")).toBe("2026-10-06");
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

  test.each(["", "   ", "-5", "100.5", "100.0", "1e5", "abc", "12a", "99999999999999999999"])(
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
// Hex colours or Tailwind arbitrary values ("p-[13px]") bypass the design tokens.
const RAW_STYLE = /#[0-9a-fA-F]{3,8}\b|\b[\w:-]+-\[[^\]]+\]/;

function sourceFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) return sourceFiles(path);
    return /\.tsx?$/.test(entry.name) && !entry.name.includes(".test.") ? [path] : [];
  });
}

test("components use only theme tokens", () => {
  const offenders = sourceFiles(SRC).filter((file) => RAW_STYLE.test(readFileSync(file, "utf8")));
  expect(offenders).toEqual([]);
});
```

`frontend/src/components/components.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { expect, test } from "vitest";
import { Button } from "./Button";
import { ErrorMessage } from "./ErrorMessage";
import { TabBar } from "./TabBar";
import { TextField } from "./TextField";
import { TransactionRow } from "./TransactionRow";

test("Button defaults to type=button and has the touch-target class", () => {
  render(<Button>Save</Button>);
  const button = screen.getByRole("button", { name: "Save" });
  expect(button).toHaveAttribute("type", "button");
  expect(button.className).toContain("min-h-touch");
});

test("TextField labels its input", () => {
  render(<TextField label="Username" />);
  expect(screen.getByLabelText("Username").className).toContain("min-h-touch");
});

test("ErrorMessage shows Error and string messages, nothing for null", () => {
  const { rerender } = render(<ErrorMessage error={null} />);
  expect(screen.queryByRole("alert")).toBeNull();
  rerender(<ErrorMessage error={new Error("Plan not found.")} />);
  expect(screen.getByRole("alert")).toHaveTextContent("Plan not found.");
  rerender(<ErrorMessage error="Choose how much risk you accept." />);
  expect(screen.getByRole("alert")).toHaveTextContent("Choose how much risk you accept.");
});

test("TabBar marks the current tab", () => {
  render(
    <MemoryRouter initialEntries={["/active"]}>
      <TabBar />
    </MemoryRouter>,
  );
  expect(screen.getByRole("navigation", { name: "Main" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "My plan" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByRole("link", { name: "Home" })).not.toHaveAttribute("aria-current");
});

test("TransactionRow signs income and shows the date", () => {
  render(
    <ul>
      <TransactionRow
        transaction={{ id: 1, booked_on: "2026-09-25", amount: 450_000, description: "Salary" }}
      />
      <TransactionRow
        transaction={{ id: 2, booked_on: "2026-09-26", amount: -12_000, description: "" }}
      />
    </ul>,
  );
  expect(screen.getByText("+450,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("-12,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("2026-09-25")).toBeInTheDocument();
  expect(screen.getByText("Transaction")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/format.test.ts src/components src/theme`
Expected: FAIL with `Failed to resolve import "./format"` / `"./Button"`. (`tokens.test.ts` passes already; that is fine.)

- [ ] **Step 3: Write the tokens**

Replace `frontend/src/theme/theme.css`:

```css
@import "tailwindcss";

/*
 * Design tokens (AGENTS.md section 7: colours and spacing only from here).
 * Hand-written; replace the values with the Figma variables when a Figma file exists.
 * `--color-*: initial` removes Tailwind's default palette, so only these colours exist.
 * Text colours meet WCAG AA (4.5:1) on canvas and surface.
 */
@theme {
  --color-*: initial;
  --color-canvas: #f4f6f5;
  --color-surface: #ffffff;
  --color-ink: #17201c;
  --color-muted: #5b6662;
  --color-line: #d9dfdc;
  --color-brand: #0b6e4f;
  --color-on-brand: #ffffff;
  --color-positive: #0b6e4f;
  --color-danger: #b42318;
  --color-warning: #8a5a00;

  --spacing-touch: 44px;
  --radius-card: 12px;
}

@layer base {
  body {
    background-color: var(--color-canvas);
    color: var(--color-ink);
  }
}
```

- [ ] **Step 4: Implement formatting**

`frontend/src/format.ts`:

```ts
/**
 * Display and input helpers. They format values from the API and parse customer input;
 * they never compute money (golden rule 2).
 */
import type { Huf } from "./api/types";

const thousands = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

export const AMOUNT_HINT = "Enter a whole number of forints, for example 250000.";

/** 73500 → "73,500 HUF", the same format as the backend explanation templates. */
export function formatHuf(amount: Huf): string {
  return `${thousands.format(amount)} HUF`;
}

/** "2026-09-01" → "2026-09". String slicing, so no time-zone shift. */
export function formatMonth(iso: string): string {
  return iso.slice(0, 7);
}

/** "2026-10-06T10:00:00Z" → "2026-10-06". */
export function formatDay(iso: string): string {
  return iso.slice(0, 10);
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

- [ ] **Step 5: Implement the components**

`frontend/src/components/Button.tsx`:

```tsx
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-brand text-on-brand",
  secondary: "border border-line bg-surface text-ink",
  danger: "border border-danger bg-surface text-danger",
};

/** Classes for a button-looking element; use on `Link` too, so links get the 44 px target. */
export function buttonClass(variant: Variant = "primary"): string {
  return `inline-flex min-h-touch min-w-touch items-center justify-center rounded-card px-4 font-semibold focus-visible:outline-2 focus-visible:outline-brand disabled:opacity-50 ${VARIANTS[variant]}`;
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

/** 44 px minimum touch target (AGENTS.md section 7). Give it visible text or an aria-label. */
export function Button({ variant = "primary", className = "", type = "button", ...props }: ButtonProps) {
  return <button type={type} className={`${buttonClass(variant)} ${className}`} {...props} />;
}
```

`frontend/src/components/TextField.tsx`:

```tsx
import type { InputHTMLAttributes } from "react";

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

/** A labelled input with a 44 px touch target. */
export function TextField({ label, className = "", ...props }: TextFieldProps) {
  return (
    <label className="block text-sm font-medium">
      {label}
      <input
        className={`mt-1 block min-h-touch w-full rounded-card border border-line bg-surface px-3 text-base text-ink ${className}`}
        {...props}
      />
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
    typeof error === "string"
      ? error
      : error instanceof Error
        ? error.message
        : "Something went wrong.";
  return (
    <p role="alert" className="rounded-card border border-danger bg-surface p-3 text-danger">
      {text}
    </p>
  );
}
```

`frontend/src/components/TabBar.tsx`:

```tsx
import { NavLink } from "react-router";

const TABS = [
  { to: "/", label: "Home", end: true },
  { to: "/questionnaire", label: "New plan", end: false },
  { to: "/active", label: "My plan", end: false },
];

export function TabBar() {
  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 border-t border-line bg-surface">
      <ul className="mx-auto flex max-w-md">
        {TABS.map((tab) => (
          <li key={tab.to} className="flex-1">
            <NavLink
              to={tab.to}
              end={tab.end}
              className={({ isActive }) =>
                `flex min-h-touch items-center justify-center text-sm ${isActive ? "font-semibold text-brand" : "text-muted"}`
              }
            >
              {tab.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
```

`frontend/src/components/Screen.tsx`:

```tsx
import type { ReactNode } from "react";
import { TabBar } from "./TabBar";

/** Mobile screen shell: title, content, bottom tab bar. */
export function Screen({ title, children }: { title: string; children: ReactNode }) {
  return (
    <>
      <main className="mx-auto max-w-md space-y-4 px-4 pt-6 pb-24">
        <h1 className="text-2xl font-bold">{title}</h1>
        {children}
      </main>
      <TabBar />
    </>
  );
}
```

`frontend/src/components/TransactionRow.tsx`:

```tsx
import type { TransactionOut } from "../api/types";
import { formatHuf } from "../format";

export function TransactionRow({ transaction }: { transaction: TransactionOut }) {
  const income = transaction.amount > 0;
  return (
    <li className="flex min-h-touch items-center justify-between gap-4 border-b border-line py-2">
      <div>
        <p>{transaction.description || "Transaction"}</p>
        <p className="text-sm text-muted">{transaction.booked_on}</p>
      </div>
      <p className={`font-semibold ${income ? "text-positive" : "text-ink"}`}>
        {income ? "+" : ""}
        {formatHuf(transaction.amount)}
      </p>
    </li>
  );
}
```

The `+` and the number are two text nodes; `getByText("+450,000 HUF")` still matches because Testing Library joins an element's text. If it does not, render `` {`${income ? "+" : ""}${formatHuf(transaction.amount)}`} `` as one string.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass.

- [ ] **Step 7: Lint, changelog**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend design tokens (`src/theme/theme.css`, default palette disabled) and shared components: Button, TextField, ErrorMessage, TabBar, Screen, TransactionRow (44 px touch targets, labelled controls).
```

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): theme tokens, formatting and shared components`

---

### Task 5: Login, logout and protected routing

Deliverable: the router, the login screen, and a guard that sends logged-out customers (or expired sessions) to `/login`.

**Files:**
- Create: `frontend/src/api/hooks.ts`, `frontend/src/screens/login/LoginScreen.tsx`
- Modify: `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, `frontend/src/main.tsx`, `frontend/src/test/render.tsx`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `apiFetch`, `ApiError` (Task 3), `makeQueryClient` (Task 3), `Screen`, `TextField`, `Button`, `ErrorMessage` (Task 4), `/api/auth/me|login|logout` (backend plan Task 1).
- Produces:
  - `hooks.ts`: `keys` (`me`, `account`, `plans`, `plan(id)`, `timeMachine(id)`, `mandate(id)`, `activePlan`, `executions`), `orNull<T>(request: Promise<T>, status: number): Promise<T | null>`, `useMe()` (data `Me | null`), `useLogin()` (mutate `LoginIn`), `useLogout()`
  - `App.tsx`: `App`, `createQueryClient(): QueryClient` (401 anywhere → `me` set to null → redirect)
  - `render.tsx`: `renderApp(url: string): QueryClient`
  - Route `/` renders a placeholder `<Screen title="Home">` until Task 6.

- [ ] **Step 1: Write the failing tests**

Replace `frontend/src/App.test.tsx`:

```tsx
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { mockApi, renderApp } from "./test/render";

const ANNA = { username: "anna", role: "customer" };
const LOGGED_OUT = { status: 401, body: { detail: "Unauthorized" } };

test("a logged-out visitor is sent to the login screen", async () => {
  mockApi({ "GET /api/auth/me": LOGGED_OUT });
  renderApp("/");
  expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
});

test("logging in opens the home screen", async () => {
  // Stateful like the real backend: /me answers 200 after login (the guard may refetch it).
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
  expect(await screen.findByRole("heading", { name: "Home" })).toBeInTheDocument();
  expect(calls.find((call) => call.method === "POST")?.body).toEqual({
    username: "anna",
    password: "secret",
  });
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
  expect(screen.getByRole("heading", { name: "Log in" })).toBeInTheDocument();
});

test("an unknown URL goes to home", async () => {
  mockApi({ "GET /api/auth/me": { body: ANNA } });
  renderApp("/nope");
  expect(await screen.findByRole("heading", { name: "Home" })).toBeInTheDocument();
});
```

Append to `frontend/src/test/render.tsx`:

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

and add the import `import { App, createQueryClient } from "../App";` at the top.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/App.test.tsx`
Expected: FAIL with `createQueryClient` is not exported / `does not provide an export named 'createQueryClient'`.

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
  plans: ["plans"],
  plan: (id: number) => ["plans", id],
  timeMachine: (id: number) => ["plans", id, "time-machine"],
  mandate: (id: number) => ["plans", id, "mandate"],
  activePlan: ["plans", "active"],
  executions: ["executions"],
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
    mutationFn: (credentials: LoginIn) =>
      apiFetch<Me>("/api/auth/login", { method: "POST", body: credentials }),
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

- [ ] **Step 4: Implement the login screen**

`frontend/src/screens/login/LoginScreen.tsx`:

```tsx
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useLogin } from "../../api/hooks";
import { Button } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { TextField } from "../../components/TextField";

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
    <main className="mx-auto max-w-md space-y-6 px-4 pt-16">
      <h1 className="text-2xl font-bold">Log in</h1>
      <p className="text-muted">SaverAI demo bank. All accounts and transfers are simulated.</p>
      <form className="space-y-4" onSubmit={submit}>
        <TextField
          label="Username"
          autoComplete="username"
          required
          value={username}
          onChange={(event) => setUsername(event.target.value)}
        />
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
        </Button>
      </form>
    </main>
  );
}
```

- [ ] **Step 5: Implement the router and the app query client**

Replace `frontend/src/App.tsx`:

```tsx
import type { QueryClient } from "@tanstack/react-query";
import { Navigate, Outlet, Route, Routes } from "react-router";
import { keys, useMe } from "./api/hooks";
import { makeQueryClient } from "./api/queryClient";
import { ErrorMessage } from "./components/ErrorMessage";
import { Screen } from "./components/Screen";
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

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginScreen />} />
      <Route element={<RequireLogin />}>
        {/* Task 6 replaces this placeholder with HomeScreen. */}
        <Route path="/" element={<Screen title="Home">{null}</Screen>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
```

Replace `frontend/src/main.tsx`:

```tsx
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
Expected: all pass (4 new App tests).

- [ ] **Step 7: Lint, changelog**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend login screen and protected routes; an expired session (401) returns the customer to login.
```

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): login screen and protected routing`

---

### Task 6: Home screen

Deliverable: home with account balance, recent transactions (`TransactionRow`), an active-plan card or a "Start a savings plan" link, and logout.

**Files:**
- Create: `frontend/src/screens/home/HomeScreen.tsx`, `frontend/src/screens/home/HomeScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `keys`, `orNull`, `useMe`, `useLogout` (Task 5), `GET /api/account` (Task 2), `GET /api/plans/active` (backend Task 13), `Screen`, `TransactionRow`, `Button`, `buttonClass`, `ErrorMessage`, `formatHuf` (Task 4), `renderScreen`, `renderApp`, `mockApi`, `plan` (Tasks 3, 5).
- Produces: `useAccount()` (data `AccountOut`), `useActivePlan()` (data `PlanOut | null`; 404 → null); `HomeScreen` at `/` (title "Home").

- [ ] **Step 1: Write the failing tests**

`frontend/src/screens/home/HomeScreen.test.tsx`:

```tsx
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { plan } from "../../test/fixtures";
import { mockApi, renderApp, renderScreen } from "../../test/render";
import { HomeScreen } from "./HomeScreen";

const ACCOUNT = {
  name: "Current account",
  balance: 600_000,
  transactions: [
    { id: 2, booked_on: "2026-09-26", amount: -12_000, description: "Groceries" },
    { id: 1, booked_on: "2026-09-25", amount: 450_000, description: "Salary" },
  ],
};
const NO_ACTIVE_PLAN = { status: 404, body: { detail: "No active plan." } };

test("shows the balance and the transactions in API order", async () => {
  mockApi({
    "GET /api/auth/me": { body: { username: "anna", role: "customer" } },
    "GET /api/account": { body: ACCOUNT },
    "GET /api/plans/active": NO_ACTIVE_PLAN,
  });
  renderScreen(<HomeScreen />);
  expect(await screen.findByText("600,000 HUF")).toBeInTheDocument();
  const rows = within(screen.getByRole("list", { name: "Recent transactions" })).getAllByRole(
    "listitem",
  );
  expect(rows).toHaveLength(2);
  expect(rows[0]).toHaveTextContent("Groceries");
  expect(rows[1]).toHaveTextContent("+450,000 HUF");
});

test("shows a start link when there is no active plan", async () => {
  mockApi({
    "GET /api/auth/me": { body: { username: "anna", role: "customer" } },
    "GET /api/account": { body: ACCOUNT },
    "GET /api/plans/active": NO_ACTIVE_PLAN,
  });
  renderScreen(<HomeScreen />);
  expect(await screen.findByRole("link", { name: "Start a savings plan" })).toHaveAttribute(
    "href",
    "/questionnaire",
  );
  expect(screen.queryByRole("alert")).toBeNull();
});

test("shows the active plan amount", async () => {
  mockApi({
    "GET /api/auth/me": { body: { username: "anna", role: "customer" } },
    "GET /api/account": { body: ACCOUNT },
    "GET /api/plans/active": { body: plan({ status: "accepted" }) },
  });
  renderScreen(<HomeScreen />);
  expect(await screen.findByText("Saving 73,500 HUF a month")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Open my plan" })).toHaveAttribute("href", "/active");
});

test("an expired session mid-flow returns to login", async () => {
  mockApi({
    "GET /api/auth/me": { body: { username: "anna", role: "customer" } },
    "GET /api/account": { status: 401, body: { detail: "Unauthorized" } },
    "GET /api/plans/active": NO_ACTIVE_PLAN,
  });
  renderApp("/");
  expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
});

test("log out calls the API and opens the login screen", async () => {
  const calls = mockApi({
    "GET /api/auth/me": { body: { username: "anna", role: "customer" } },
    "GET /api/account": { body: ACCOUNT },
    "GET /api/plans/active": NO_ACTIVE_PLAN,
    "POST /api/auth/logout": { body: { ok: true } },
  });
  renderScreen(<HomeScreen />);
  await userEvent.setup().click(await screen.findByRole("button", { name: "Log out" }));
  expect(await screen.findByText("Navigated to /login")).toBeInTheDocument();
  expect(calls.some((call) => call.method === "POST" && call.path === "/api/auth/logout")).toBe(
    true,
  );
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/screens/home`
Expected: FAIL with `Failed to resolve import "./HomeScreen"`.

- [ ] **Step 3: Add the hooks**

Append to `frontend/src/api/hooks.ts` (and add `AccountOut`, `PlanOut` to the `./types` import):

```ts
export function useAccount() {
  return useQuery({ queryKey: keys.account, queryFn: () => apiFetch<AccountOut>("/api/account") });
}

/** The accepted or paused plan, or null when the customer has none (API 404). */
export function useActivePlan() {
  return useQuery({
    queryKey: keys.activePlan,
    queryFn: () => orNull(apiFetch<PlanOut>("/api/plans/active"), 404),
  });
}
```

- [ ] **Step 4: Implement the screen**

`frontend/src/screens/home/HomeScreen.tsx`:

```tsx
import { Link, useNavigate } from "react-router";
import { useAccount, useActivePlan, useLogout, useMe } from "../../api/hooks";
import { Button, buttonClass } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Screen } from "../../components/Screen";
import { TransactionRow } from "../../components/TransactionRow";
import { formatHuf } from "../../format";

export function HomeScreen() {
  const me = useMe();
  const account = useAccount();
  const active = useActivePlan();
  const logout = useLogout();
  const navigate = useNavigate();

  return (
    <Screen title="Home">
      {me.data && <p className="text-muted">Hello, {me.data.username}</p>}

      <section className="rounded-card bg-surface p-4">
        <h2 className="text-sm text-muted">{account.data?.name ?? "Current account"}</h2>
        {account.isPending && <p>Loading…</p>}
        <ErrorMessage error={account.error} />
        {account.isSuccess && (
          <p className="text-3xl font-bold">{formatHuf(account.data.balance)}</p>
        )}
      </section>

      <section className="space-y-2 rounded-card bg-surface p-4">
        <ErrorMessage error={active.error} />
        {active.data && (
          <>
            <p className="font-semibold">Saving {formatHuf(active.data.monthly_amount)} a month</p>
            <Link to="/active" className={buttonClass("secondary")}>
              Open my plan
            </Link>
          </>
        )}
        {active.isSuccess && active.data === null && (
          <>
            <p>No savings plan yet.</p>
            <Link to="/questionnaire" className={buttonClass("primary")}>
              Start a savings plan
            </Link>
          </>
        )}
      </section>

      {account.isSuccess && (
        <section>
          <h2 className="mb-2 text-lg font-semibold">Recent transactions</h2>
          <ul aria-label="Recent transactions">
            {account.data.transactions.map((transaction) => (
              <TransactionRow key={transaction.id} transaction={transaction} />
            ))}
          </ul>
        </section>
      )}

      <Button
        variant="secondary"
        disabled={logout.isPending}
        onClick={() => logout.mutate(undefined, { onSettled: () => navigate("/login") })}
      >
        Log out
      </Button>
    </Screen>
  );
}
```

`"Saving {formatHuf(...)} a month"` renders as several text nodes inside one `<p>`; `findByText("Saving 73,500 HUF a month")` matches the element's joined text.

- [ ] **Step 5: Wire the route**

In `frontend/src/App.tsx`, import `HomeScreen` from `./screens/home/HomeScreen`, replace the placeholder route with `<Route path="/" element={<HomeScreen />} />`, and remove the now unused `Screen` import.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass. (The Task 5 login test now renders HomeScreen with unmocked account calls; it still finds the "Home" heading.)

- [ ] **Step 7: Lint, changelog**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend home screen: balance, recent transactions, active plan or a link to start one.
```

Run: `cd frontend && npm run fmt && npm run lint`. Expected: clean.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): home screen with balance and transactions`

---

### Task 7: Questionnaire with no-surplus and too-little-data states (AC5, AC6, AC8)

Deliverable: the fixed questionnaire. On submit it stores the answers and asks for a proposal. A plan opens the plan review; no surplus shows the backend explanation (AC5); too little data shows the explanation and asks for the expected monthly savings, then resubmits (AC6). Invalid amounts never reach the API; server errors (past date) are shown (AC8).

**Files:**
- Create: `frontend/src/screens/questionnaire/QuestionnaireScreen.tsx`, `frontend/src/screens/questionnaire/QuestionnaireScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `docs/traceability.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `POST /api/questionnaire`, `POST /api/plans` (backend Task 13), `Screen`, `TextField`, `Button`, `buttonClass`, `ErrorMessage`, `parseHuf`, `AMOUNT_HINT` (Task 4), `mockApi`, `renderScreen`, `plan` (Task 3).
- Produces: `useProposePlan()` (mutate `QuestionnaireIn` → `ProposalOut`); `QuestionnaireScreen` at `/questionnaire` (title "New plan"); field labels "Existing emergency fund (HUF)", "Expense N name", "Expense N amount (HUF)", "Expense N due date", "Expected monthly savings (HUF)"; risk labels starting "1 –" … "5 –"; submit button "Show my plan".

- [ ] **Step 1: Write the failing tests**

`frontend/src/screens/questionnaire/QuestionnaireScreen.test.tsx`:

```tsx
import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { ProposalOut } from "../../api/types";
import { PLAN } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { QuestionnaireScreen } from "./QuestionnaireScreen";

type User = ReturnType<typeof userEvent.setup>;

const STORED = { status: 201, body: { id: 1 } };
const PROPOSED: ProposalOut = { outcome: "plan", plan: PLAN, explanations: PLAN.explanations };
const NO_SURPLUS: ProposalOut = {
  outcome: "no_surplus",
  plan: null,
  explanations: [
    "Your median monthly surplus over the last 6 months is -40,000 HUF, so there is no surplus to save. No investment plan was created.",
  ],
};
const NEEDS_SAVINGS: ProposalOut = {
  outcome: "needs_expected_savings",
  plan: null,
  explanations: [
    "We found only 2 full months of transactions; at least 3 are needed for an estimate. Please enter how much you expect to save each month.",
  ],
};

function start() {
  renderScreen(<QuestionnaireScreen />, { path: "/questionnaire" });
  return userEvent.setup();
}

async function fillBasics(user: User, fund = "750000") {
  await user.click(screen.getByLabelText("3 – Balanced"));
  await user.type(screen.getByLabelText("Existing emergency fund (HUF)"), fund);
}

async function submit(user: User) {
  await user.click(screen.getByRole("button", { name: "Show my plan" }));
}

test("sends whole-forint answers and opens the proposed plan", async () => {
  const calls = mockApi({ "POST /api/questionnaire": STORED, "POST /api/plans": { body: PROPOSED } });
  const user = start();
  await fillBasics(user);
  await user.click(screen.getByRole("button", { name: "Add planned expense" }));
  await user.type(screen.getByLabelText("Expense 1 name"), "Car");
  await user.type(screen.getByLabelText("Expense 1 amount (HUF)"), "500 000");
  fireEvent.change(screen.getByLabelText("Expense 1 due date"), { target: { value: "2027-08-15" } });
  await submit(user);

  expect(await screen.findByText("Navigated to /plans/7")).toBeInTheDocument();
  expect(calls[0]?.body).toEqual({
    risk_score: 3,
    existing_emergency_fund: 750_000,
    expected_monthly_savings: null,
    planned_expenses: [{ name: "Car", amount: 500_000, due_on: "2027-08-15" }],
  });
  expect(calls[1]).toMatchObject({ method: "POST", path: "/api/plans" });
});

test("test_ac5_no_surplus_shows_explanation_without_plan", async () => {
  mockApi({ "POST /api/questionnaire": STORED, "POST /api/plans": { body: NO_SURPLUS } });
  const user = start();
  await fillBasics(user, "0");
  await submit(user);

  expect(await screen.findByRole("status")).toHaveTextContent("so there is no surplus to save");
  expect(screen.queryByText(/Navigated to/)).toBeNull();
  expect(screen.queryByLabelText("Expected monthly savings (HUF)")).toBeNull();
  expect(screen.getByRole("link", { name: "Back to home" })).toHaveAttribute("href", "/");
});

test("test_ac6_too_little_data_asks_for_expected_savings_and_resubmits", async () => {
  const proposals = [NEEDS_SAVINGS, PROPOSED];
  const calls = mockApi({
    "POST /api/questionnaire": STORED,
    "POST /api/plans": () => ({ body: proposals.shift() }),
  });
  const user = start();
  await fillBasics(user);
  await submit(user);

  expect(await screen.findByRole("status")).toHaveTextContent("Please enter how much you expect");
  await user.type(screen.getByLabelText("Expected monthly savings (HUF)"), "40000");
  await submit(user);

  expect(await screen.findByText("Navigated to /plans/7")).toBeInTheDocument();
  const answers = calls.filter((call) => call.path === "/api/questionnaire");
  expect(answers).toHaveLength(2);
  expect(answers[1]?.body).toMatchObject({
    risk_score: 3,
    existing_emergency_fund: 750_000,
    expected_monthly_savings: 40_000,
  });
});

test("test_ac8_negative_amount_shows_error_and_sends_nothing", async () => {
  const calls = mockApi({});
  const user = start();
  await fillBasics(user, "-5");
  await submit(user);

  expect(screen.getByRole("alert")).toHaveTextContent("Existing emergency fund");
  expect(screen.getByRole("alert")).toHaveTextContent("whole number of forints");
  expect(calls).toHaveLength(0);
});

test("rejects a decimal amount without calling the API", async () => {
  const calls = mockApi({});
  const user = start();
  await fillBasics(user);
  await user.click(screen.getByRole("button", { name: "Add planned expense" }));
  await user.type(screen.getByLabelText("Expense 1 name"), "Car");
  await user.type(screen.getByLabelText("Expense 1 amount (HUF)"), "100.5");
  fireEvent.change(screen.getByLabelText("Expense 1 due date"), { target: { value: "2027-08-15" } });
  await submit(user);

  expect(screen.getByRole("alert")).toHaveTextContent("Expense 1");
  expect(calls).toHaveLength(0);
});

test("asks for a risk answer first", async () => {
  const calls = mockApi({});
  const user = start();
  await user.type(screen.getByLabelText("Existing emergency fund (HUF)"), "0");
  await submit(user);
  expect(screen.getByRole("alert")).toHaveTextContent("Choose how much risk you accept.");
  expect(calls).toHaveLength(0);
});

test("test_ac8_past_expense_date_shows_server_message", async () => {
  mockApi({
    "POST /api/questionnaire": {
      status: 422,
      body: { detail: "The expense date 2026-10-05 is in the past." },
    },
  });
  const user = start();
  await fillBasics(user);
  await user.click(screen.getByRole("button", { name: "Add planned expense" }));
  await user.type(screen.getByLabelText("Expense 1 name"), "Car");
  await user.type(screen.getByLabelText("Expense 1 amount (HUF)"), "500000");
  fireEvent.change(screen.getByLabelText("Expense 1 due date"), { target: { value: "2026-10-05" } });
  await submit(user);

  expect(await screen.findByRole("alert")).toHaveTextContent("is in the past");
  expect(screen.queryByText(/Navigated to/)).toBeNull();
});

test("an expense row can be removed", async () => {
  mockApi({});
  const user = start();
  await user.click(screen.getByRole("button", { name: "Add planned expense" }));
  await user.click(screen.getByRole("button", { name: "Remove expense 1" }));
  expect(screen.queryByLabelText("Expense 1 name")).toBeNull();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/screens/questionnaire`
Expected: FAIL with `Failed to resolve import "./QuestionnaireScreen"`.

- [ ] **Step 3: Add the hook**

Append to `frontend/src/api/hooks.ts` (add `IdOut`, `ProposalOut`, `QuestionnaireIn` to the `./types` import):

```ts
/** Store the answers, then ask the rule engine for a proposal (plan, no surplus, or needs data). */
export function useProposePlan() {
  return useMutation({
    mutationFn: async (answers: QuestionnaireIn) => {
      await apiFetch<IdOut>("/api/questionnaire", { method: "POST", body: answers });
      return apiFetch<ProposalOut>("/api/plans", { method: "POST" });
    },
  });
}
```

- [ ] **Step 4: Implement the screen**

`frontend/src/screens/questionnaire/QuestionnaireScreen.tsx`:

```tsx
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { useProposePlan } from "../../api/hooks";
import type { ExpenseIn, Huf, ProposalOut, QuestionnaireIn } from "../../api/types";
import { Button, buttonClass } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Screen } from "../../components/Screen";
import { TextField } from "../../components/TextField";
import { AMOUNT_HINT, parseHuf } from "../../format";

/** Fixed questions with validated answers (no AI at runtime). */
const RISK_OPTIONS = [
  { score: 1, label: "1 – I do not want to lose any money" },
  { score: 2, label: "2 – Small, short-lived losses are fine" },
  { score: 3, label: "3 – Balanced" },
  { score: 4, label: "4 – Larger swings for a higher return" },
  { score: 5, label: "5 – Highest risk, long horizon" },
];

interface ExpenseRow {
  key: number;
  name: string;
  amount: string;
  dueOn: string;
}

export function QuestionnaireScreen() {
  const navigate = useNavigate();
  const propose = useProposePlan();
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [fund, setFund] = useState("");
  const [expenses, setExpenses] = useState<ExpenseRow[]>([]);
  const [nextKey, setNextKey] = useState(1);
  const [expected, setExpected] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [result, setResult] = useState<ProposalOut | null>(null);
  const needsExpected = result?.outcome === "needs_expected_savings";

  /** The request body, or a message naming the first invalid answer. */
  function answers(): QuestionnaireIn | string {
    if (riskScore === null) return "Choose how much risk you accept.";
    const existingFund = parseHuf(fund);
    if (existingFund === null) return `Existing emergency fund: ${AMOUNT_HINT}`;
    const planned: ExpenseIn[] = [];
    for (const [index, row] of expenses.entries()) {
      const amount = parseHuf(row.amount);
      if (row.name.trim() === "" || row.dueOn === "" || amount === null) {
        return `Expense ${index + 1}: fill in the name and the due date. ${AMOUNT_HINT}`;
      }
      planned.push({ name: row.name.trim(), amount, due_on: row.dueOn });
    }
    let expectedSavings: Huf | null = null;
    if (needsExpected) {
      expectedSavings = parseHuf(expected);
      if (expectedSavings === null) return `Expected monthly savings: ${AMOUNT_HINT}`;
    }
    return {
      risk_score: riskScore,
      existing_emergency_fund: existingFund,
      expected_monthly_savings: expectedSavings,
      planned_expenses: planned,
    };
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const body = answers();
    if (typeof body === "string") {
      setFormError(body);
      return;
    }
    setFormError(null);
    propose.mutate(body, {
      onSuccess: (proposal) => {
        if (proposal.plan !== null) navigate(`/plans/${proposal.plan.id}`);
        else setResult(proposal);
      },
    });
  }

  function addExpense() {
    setExpenses((rows) => [...rows, { key: nextKey, name: "", amount: "", dueOn: "" }]);
    setNextKey((key) => key + 1);
  }

  function updateExpense(key: number, change: Partial<ExpenseRow>) {
    setExpenses((rows) => rows.map((row) => (row.key === key ? { ...row, ...change } : row)));
  }

  return (
    <Screen title="New plan">
      <form className="space-y-5" onSubmit={submit} noValidate>
        <fieldset className="space-y-1">
          <legend className="mb-2 font-semibold">How much risk do you accept?</legend>
          {RISK_OPTIONS.map((option) => (
            <label
              key={option.score}
              className="flex min-h-touch items-center gap-3 rounded-card border border-line bg-surface px-3"
            >
              <input
                type="radio"
                name="risk"
                value={option.score}
                checked={riskScore === option.score}
                onChange={() => setRiskScore(option.score)}
              />
              {option.label}
            </label>
          ))}
        </fieldset>

        <TextField
          label="Existing emergency fund (HUF)"
          inputMode="numeric"
          value={fund}
          onChange={(event) => setFund(event.target.value)}
        />

        <fieldset className="space-y-3">
          <legend className="mb-2 font-semibold">Planned large expenses</legend>
          {expenses.map((row, index) => (
            <div key={row.key} className="space-y-2 rounded-card border border-line bg-surface p-3">
              <TextField
                label={`Expense ${index + 1} name`}
                value={row.name}
                onChange={(event) => updateExpense(row.key, { name: event.target.value })}
              />
              <TextField
                label={`Expense ${index + 1} amount (HUF)`}
                inputMode="numeric"
                value={row.amount}
                onChange={(event) => updateExpense(row.key, { amount: event.target.value })}
              />
              <TextField
                label={`Expense ${index + 1} due date`}
                type="date"
                value={row.dueOn}
                onChange={(event) => updateExpense(row.key, { dueOn: event.target.value })}
              />
              <Button
                variant="secondary"
                onClick={() => setExpenses((rows) => rows.filter((r) => r.key !== row.key))}
              >
                Remove expense {index + 1}
              </Button>
            </div>
          ))}
          <Button variant="secondary" onClick={addExpense}>
            Add planned expense
          </Button>
        </fieldset>

        {result !== null && (
          <section role="status" className="space-y-2 rounded-card border border-warning bg-surface p-4">
            {result.explanations.map((text) => (
              <p key={text}>{text}</p>
            ))}
          </section>
        )}

        {needsExpected && (
          <TextField
            label="Expected monthly savings (HUF)"
            inputMode="numeric"
            value={expected}
            onChange={(event) => setExpected(event.target.value)}
          />
        )}

        <ErrorMessage error={formError ?? propose.error} />
        <Button type="submit" className="w-full" disabled={propose.isPending}>
          Show my plan
        </Button>
        {result?.outcome === "no_surplus" && (
          <Link to="/" className={buttonClass("secondary")}>
            Back to home
          </Link>
        )}
      </form>
    </Screen>
  );
}
```

- [ ] **Step 5: Wire the route**

In `frontend/src/App.tsx`, import `QuestionnaireScreen` and add inside the `RequireLogin` route:

```tsx
        <Route path="/questionnaire" element={<QuestionnaireScreen />} />
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass (8 questionnaire tests).

- [ ] **Step 7: Traceability, changelog, lint**

In `docs/traceability.md`, append to the evidence cells:
- AC5: `; frontend/src/screens/questionnaire/QuestionnaireScreen.test.tsx::test_ac5_no_surplus_shows_explanation_without_plan`
- AC6: `; frontend/src/screens/questionnaire/QuestionnaireScreen.test.tsx::test_ac6_too_little_data_asks_for_expected_savings_and_resubmits`
- AC8: `; frontend/src/screens/questionnaire/QuestionnaireScreen.test.tsx::test_ac8_negative_amount_shows_error_and_sends_nothing; frontend/src/screens/questionnaire/QuestionnaireScreen.test.tsx::test_ac8_past_expense_date_shows_server_message`

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend questionnaire: fixed questions, whole-forint validation, no-surplus explanation (AC5), expected-savings question when data is too short (AC6), server validation messages (AC8).
```

Run: `cd frontend && npm run fmt && npm run lint && cd .. && make docs-check`. Expected: clean, `docs-check: OK`.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): questionnaire with no-surplus and too-little-data states (AC5, AC6, AC8)`

---

### Task 8: Plan review with confidence, edit amount and reject (AC6, AC7, AC8)

Deliverable: the plan review screen: monthly amount, confidence level, approval note, backend explanations, plan items; for a proposed plan: lower the amount, open the time machine, review the mandate, reject.

**Files:**
- Create: `frontend/src/components/PlanItemList.tsx`, `frontend/src/screens/plan-review/PlanReviewScreen.tsx`, `frontend/src/screens/plan-review/PlanReviewScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `docs/traceability.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `GET /api/plans/{id}`, `PATCH /api/plans/{id}`, `POST /api/plans/{id}/reject` (backend Task 13), `keys` (Task 5), components and `parseHuf`, `AMOUNT_HINT`, `formatHuf` (Task 4), `plan`, `mockApi`, `renderScreen` (Task 3).
- Produces: `usePlan(id: number)`, `useEditPlan(id: number)` (mutate `Huf`), `usePlanAction(action: "accept" | "reject" | "pause")` (mutate `planId: number` → `PlanOut`; updates `keys.plan(id)`, invalidates `keys.plans` and `keys.executions`); `PlanItemList({ items: PlanItemOut[] })`; `PlanReviewScreen` at `/plans/:planId` (title "Your plan"); links "Replay on my history (time machine)" and "Review mandate and accept".

- [ ] **Step 1: Write the failing tests**

`frontend/src/screens/plan-review/PlanReviewScreen.test.tsx`:

```tsx
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { PlanOut } from "../../api/types";
import { plan } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { PlanReviewScreen } from "./PlanReviewScreen";

function start() {
  renderScreen(<PlanReviewScreen />, { path: "/plans/:planId", url: "/plans/7" });
  return userEvent.setup();
}

test("shows the amount, confidence, explanations and items", async () => {
  mockApi({ "GET /api/plans/7": { body: plan() } });
  start();
  expect(await screen.findByText("73,500 HUF", { selector: "p" })).toBeInTheDocument();
  expect(screen.getByText("Normal")).toBeInTheDocument();
  expect(screen.getByText(/70% of your median monthly surplus/)).toBeInTheDocument();
  expect(screen.getByText(/Balanced fund · risk 3 · not liquid/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Replay on my history (time machine)" })).toHaveAttribute(
    "href",
    "/plans/7/time-machine",
  );
  expect(screen.getByRole("link", { name: "Review mandate and accept" })).toHaveAttribute(
    "href",
    "/plans/7/mandate",
  );
});

test("test_ac6_low_confidence_is_shown_with_approval_note", async () => {
  mockApi({
    "GET /api/plans/7": {
      body: plan({
        confidence: "low",
        per_transfer_approval: true,
        explanations: [
          "This plan is based on only 4 months of data, so its confidence is low. Every transfer will ask for your approval.",
        ],
      }),
    },
  });
  start();
  expect(await screen.findByText("Low")).toBeInTheDocument();
  expect(screen.getByText("Every transfer needs your approval.")).toBeInTheDocument();
  expect(screen.getByText(/only 4 months of data/)).toBeInTheDocument();
});

test("lowering the amount sends an integer and shows the revised plan", async () => {
  let current: PlanOut = plan();
  const calls = mockApi({
    "GET /api/plans/7": () => ({ body: current }),
    "PATCH /api/plans/7": (body) => {
      current = plan({ monthly_amount: (body as { monthly_amount: number }).monthly_amount });
      return { body: current };
    },
  });
  const user = start();
  await user.type(await screen.findByLabelText("Lower the monthly amount (HUF)"), "50 000");
  await user.click(screen.getByRole("button", { name: "Update amount" }));

  expect(await screen.findByText("50,000 HUF", { selector: "p" })).toBeInTheDocument();
  expect(calls.find((call) => call.method === "PATCH")?.body).toEqual({ monthly_amount: 50_000 });
});

test("test_ac8_amount_above_proposal_shows_server_message", async () => {
  mockApi({
    "GET /api/plans/7": { body: plan() },
    "PATCH /api/plans/7": {
      status: 422,
      body: { detail: "The monthly amount must be between 1 and 73500 HUF." },
    },
  });
  const user = start();
  await user.type(await screen.findByLabelText("Lower the monthly amount (HUF)"), "80000");
  await user.click(screen.getByRole("button", { name: "Update amount" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("between 1 and 73500 HUF");
});

test("an invalid amount is not sent", async () => {
  const calls = mockApi({ "GET /api/plans/7": { body: plan() } });
  const user = start();
  await user.type(await screen.findByLabelText("Lower the monthly amount (HUF)"), "-5");
  await user.click(screen.getByRole("button", { name: "Update amount" }));
  expect(screen.getByRole("alert")).toHaveTextContent("whole number of forints");
  expect(calls.filter((call) => call.method === "PATCH")).toHaveLength(0);
});

test("test_ac7_rejected_plan_offers_no_accept", async () => {
  let current: PlanOut = plan();
  const calls = mockApi({
    "GET /api/plans/7": () => ({ body: current }),
    "POST /api/plans/7/reject": () => {
      current = plan({ status: "rejected" });
      return { body: current };
    },
  });
  const user = start();
  await user.click(await screen.findByRole("button", { name: "Reject plan" }));

  expect(await screen.findByText("This plan is rejected.")).toBeInTheDocument();
  expect(screen.queryByRole("link", { name: "Review mandate and accept" })).toBeNull();
  expect(screen.getByRole("link", { name: "Start a new questionnaire" })).toBeInTheDocument();
  expect(calls.filter((call) => call.path.endsWith("/accept"))).toHaveLength(0);
});

test("another customer's plan shows the 403 message", async () => {
  mockApi({
    "GET /api/plans/7": { status: 403, body: { detail: "This plan belongs to another customer." } },
  });
  start();
  expect(await screen.findByRole("alert")).toHaveTextContent("belongs to another customer");
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/screens/plan-review`
Expected: FAIL with `Failed to resolve import "./PlanReviewScreen"`.

- [ ] **Step 3: Add the hooks**

Append to `frontend/src/api/hooks.ts` (add `Huf` to the `./types` import; `PlanOut` is already there):

```ts
export function usePlan(planId: number) {
  return useQuery({
    queryKey: keys.plan(planId),
    queryFn: () => apiFetch<PlanOut>(`/api/plans/${planId}`),
  });
}

/** Lower the monthly amount of a proposed plan; the backend re-runs the allocation. */
export function useEditPlan(planId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (monthlyAmount: Huf) =>
      apiFetch<PlanOut>(`/api/plans/${planId}`, {
        method: "PATCH",
        body: { monthly_amount: monthlyAmount },
      }),
    onSuccess: (updated) => {
      client.setQueryData(keys.plan(planId), updated);
      void client.invalidateQueries({ queryKey: keys.timeMachine(planId) });
      void client.invalidateQueries({ queryKey: keys.mandate(planId) });
    },
  });
}

/** Accept (signs the mandate, creates orders once — AC7), reject or pause a plan. */
export function usePlanAction(action: "accept" | "reject" | "pause") {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (planId: number) =>
      apiFetch<PlanOut>(`/api/plans/${planId}/${action}`, { method: "POST" }),
    onSuccess: (updated) => {
      client.setQueryData(keys.plan(updated.id), updated);
      void client.invalidateQueries({ queryKey: keys.plans });
      void client.invalidateQueries({ queryKey: keys.executions });
    },
  });
}
```

- [ ] **Step 4: Implement the item list and the screen**

`frontend/src/components/PlanItemList.tsx`:

```tsx
import type { PlanItemOut } from "../api/types";
import { formatHuf } from "../format";

/** Plan lines in the rule engine's priority order: emergency fund, expenses, investment. */
export function PlanItemList({ items }: { items: PlanItemOut[] }) {
  return (
    <ul className="space-y-2">
      {items.map((item, index) => (
        <li key={`${index}-${item.label}`} className="rounded-card border border-line bg-surface p-3">
          <div className="flex justify-between gap-4 font-semibold">
            <span>{item.label}</span>
            <span>{formatHuf(item.monthly_amount)}</span>
          </div>
          <p className="text-sm text-muted">
            {item.product.name} · risk {item.product.risk_level} ·{" "}
            {item.product.liquid ? "liquid" : "not liquid"}
          </p>
          {item.target_amount !== null && (
            <p className="text-sm text-muted">Target: {formatHuf(item.target_amount)}</p>
          )}
        </li>
      ))}
    </ul>
  );
}
```

`frontend/src/screens/plan-review/PlanReviewScreen.tsx`:

```tsx
import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router";
import { useEditPlan, usePlan, usePlanAction } from "../../api/hooks";
import type { Confidence } from "../../api/types";
import { Button, buttonClass } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { PlanItemList } from "../../components/PlanItemList";
import { Screen } from "../../components/Screen";
import { TextField } from "../../components/TextField";
import { AMOUNT_HINT, formatHuf, parseHuf } from "../../format";

const CONFIDENCE_LABEL: Record<Confidence, string> = {
  normal: "Normal",
  low: "Low",
  none: "No estimate – based on your expected savings",
};

export function PlanReviewScreen() {
  const planId = Number(useParams().planId);
  const plan = usePlan(planId);
  const edit = useEditPlan(planId);
  const reject = usePlanAction("reject");
  const [amount, setAmount] = useState("");
  const [amountError, setAmountError] = useState<string | null>(null);

  function lowerAmount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = parseHuf(amount);
    if (value === null) {
      setAmountError(AMOUNT_HINT);
      return;
    }
    setAmountError(null);
    edit.mutate(value, { onSuccess: () => setAmount("") });
  }

  if (!plan.isSuccess) {
    return (
      <Screen title="Your plan">
        {plan.isError ? <ErrorMessage error={plan.error} /> : <p>Loading…</p>}
      </Screen>
    );
  }
  const current = plan.data;
  const proposed = current.status === "proposed";

  return (
    <Screen title="Your plan">
      <section className="rounded-card bg-surface p-4">
        <p className="text-3xl font-bold">{formatHuf(current.monthly_amount)}</p>
        <p className="text-muted">per month</p>
        <p className="mt-2">
          Confidence: <strong>{CONFIDENCE_LABEL[current.confidence]}</strong>
        </p>
        {current.per_transfer_approval && <p>Every transfer needs your approval.</p>}
      </section>

      <section className="space-y-2">
        {current.explanations.map((text) => (
          <p key={text}>{text}</p>
        ))}
      </section>

      <PlanItemList items={current.items} />

      {!proposed && (
        <p role="status" className="font-semibold">
          This plan is {current.status}.
        </p>
      )}

      {proposed && (
        <>
          <form className="space-y-2" onSubmit={lowerAmount} noValidate>
            <TextField
              label="Lower the monthly amount (HUF)"
              inputMode="numeric"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />
            <Button type="submit" variant="secondary" disabled={edit.isPending}>
              Update amount
            </Button>
          </form>
          <ErrorMessage error={amountError ?? edit.error} />
          <Link to={`/plans/${current.id}/time-machine`} className={buttonClass("secondary")}>
            Replay on my history (time machine)
          </Link>
          <Link to={`/plans/${current.id}/mandate`} className={buttonClass("primary")}>
            Review mandate and accept
          </Link>
          <ErrorMessage error={reject.error} />
          <Button variant="danger" disabled={reject.isPending} onClick={() => reject.mutate(current.id)}>
            Reject plan
          </Button>
        </>
      )}

      {current.status === "rejected" && (
        <Link to="/questionnaire" className={buttonClass("secondary")}>
          Start a new questionnaire
        </Link>
      )}
    </Screen>
  );
}
```

`"This plan is {current.status}."` renders as joined text "This plan is rejected."; the test matches the `<p>`.

- [ ] **Step 5: Wire the route**

In `frontend/src/App.tsx`, import `PlanReviewScreen` and add inside the `RequireLogin` route:

```tsx
        <Route path="/plans/:planId" element={<PlanReviewScreen />} />
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass (7 plan review tests).

- [ ] **Step 7: Traceability, changelog, lint**

In `docs/traceability.md`, append to the evidence cells:
- AC6: `; frontend/src/screens/plan-review/PlanReviewScreen.test.tsx::test_ac6_low_confidence_is_shown_with_approval_note`
- AC7: `; frontend/src/screens/plan-review/PlanReviewScreen.test.tsx::test_ac7_rejected_plan_offers_no_accept`
- AC8: `; frontend/src/screens/plan-review/PlanReviewScreen.test.tsx::test_ac8_amount_above_proposal_shows_server_message`

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend plan review: amount, confidence level and approval note (AC6), explanations, plan items, lowering the amount, rejecting (AC7), server validation messages (AC8).
```

Run: `cd frontend && npm run fmt && npm run lint && cd .. && make docs-check`. Expected: clean, `docs-check: OK`.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): plan review with confidence, edit and reject (AC6, AC7, AC8)`

---

### Task 9: Time machine screen (AC4)

Deliverable: the plan replayed on the customer's history: total saved, a bar chart of savings to date with skipped months in the danger colour, and a month list where skipped months say "Skipped" with the backend's note.

**Files:**
- Create: `frontend/src/screens/time-machine/TimeMachineScreen.tsx`, `frontend/src/screens/time-machine/TimeMachineScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `frontend/src/test/setup.ts`, `docs/traceability.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `GET /api/plans/{id}/time-machine` (backend Task 13), `keys` (Task 5), `Screen`, `ErrorMessage`, `buttonClass`, `formatHuf`, `formatMonth` (Task 4).
- Produces: `useTimeMachine(planId: number)`; `TimeMachineScreen` at `/plans/:planId/time-machine` (title "Time machine"); month list as an `<ol>`; link "Back to plan".

- [ ] **Step 1: Write the failing test**

`frontend/src/screens/time-machine/TimeMachineScreen.test.tsx`:

```tsx
import { screen, within } from "@testing-library/react";
import { expect, test } from "vitest";
import type { TimeMachineOut } from "../../api/types";
import { mockApi, renderScreen } from "../../test/render";
import { TimeMachineScreen } from "./TimeMachineScreen";

const NOTE =
  "2026-05: the transfer was skipped because it would have left less than 100,000 HUF on your account.";

const MACHINE: TimeMachineOut = {
  total_saved: 73_500,
  skipped_months: ["2026-05-01"],
  months: [
    {
      month: "2026-04-01",
      balance_before_transfer: 400_000,
      transfer: 73_500,
      skipped: false,
      balance_after: 326_500,
      saved_to_date: 73_500,
      note: null,
    },
    {
      month: "2026-05-01",
      balance_before_transfer: 150_000,
      transfer: 0,
      skipped: true,
      balance_after: 150_000,
      saved_to_date: 73_500,
      note: NOTE,
    },
  ],
};

function start() {
  renderScreen(<TimeMachineScreen />, {
    path: "/plans/:planId/time-machine",
    url: "/plans/7/time-machine",
  });
}

test("test_ac4_skipped_month_is_flagged_with_backend_note", async () => {
  mockApi({ "GET /api/plans/7/time-machine": { body: MACHINE } });
  start();

  const months = within(await screen.findByRole("list", { name: "Months" })).getAllByRole(
    "listitem",
  );
  expect(months).toHaveLength(2);
  expect(months[0]).toHaveTextContent("2026-04");
  expect(months[0]).toHaveTextContent("+73,500 HUF");
  expect(months[0]).not.toHaveTextContent("Skipped");
  expect(months[1]).toHaveTextContent("Skipped");
  expect(months[1]).toHaveTextContent(NOTE);
  expect(screen.getByText("Skipped months: 1")).toBeInTheDocument();
});

test("shows the total saved and that it is not a forecast", async () => {
  mockApi({ "GET /api/plans/7/time-machine": { body: MACHINE } });
  start();
  expect(await screen.findByText("Saved: 73,500 HUF")).toBeInTheDocument();
  expect(screen.getByText(/past behaviour only, not a forecast/)).toBeInTheDocument();
  expect(screen.getByRole("img", { name: /Savings to date per month/ })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Back to plan" })).toHaveAttribute("href", "/plans/7");
});

test("shows the backend error when the replay is impossible", async () => {
  mockApi({
    "GET /api/plans/7/time-machine": {
      status: 409,
      body: { detail: "No account found for this customer." },
    },
  });
  start();
  expect(await screen.findByRole("alert")).toHaveTextContent("No account found");
});
```

AC4 is asserted on the month list, not on the SVG: Recharts' `ResponsiveContainer` renders at zero size in jsdom.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/screens/time-machine`
Expected: FAIL with `Failed to resolve import "./TimeMachineScreen"`.

- [ ] **Step 3: Stub ResizeObserver for Recharts**

Append to `frontend/src/test/setup.ts`:

```ts
// Recharts' ResponsiveContainer needs ResizeObserver, which jsdom lacks.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
globalThis.ResizeObserver = ResizeObserverStub;
```

- [ ] **Step 4: Add the hook**

Append to `frontend/src/api/hooks.ts` (add `TimeMachineOut` to the `./types` import):

```ts
export function useTimeMachine(planId: number) {
  return useQuery({
    queryKey: keys.timeMachine(planId),
    queryFn: () => apiFetch<TimeMachineOut>(`/api/plans/${planId}/time-machine`),
  });
}
```

- [ ] **Step 5: Implement the screen**

`frontend/src/screens/time-machine/TimeMachineScreen.tsx`:

```tsx
import { Link, useParams } from "react-router";
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { useTimeMachine } from "../../api/hooks";
import { buttonClass } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Screen } from "../../components/Screen";
import { formatHuf, formatMonth } from "../../format";

/** AC4: the plan replayed on stored transactions. Every number comes from the backend. */
export function TimeMachineScreen() {
  const planId = Number(useParams().planId);
  const machine = useTimeMachine(planId);

  if (!machine.isSuccess) {
    return (
      <Screen title="Time machine">
        {machine.isError ? <ErrorMessage error={machine.error} /> : <p>Loading…</p>}
        <Link to={`/plans/${planId}`} className={buttonClass("secondary")}>
          Back to plan
        </Link>
      </Screen>
    );
  }
  const { months, total_saved: totalSaved, skipped_months: skipped } = machine.data;

  return (
    <Screen title="Time machine">
      <p className="text-muted">
        Your plan replayed on your stored transactions. This shows past behaviour only, not a
        forecast.
      </p>
      <section className="rounded-card bg-surface p-4">
        <p className="text-xl font-bold">Saved: {formatHuf(totalSaved)}</p>
        <p className={skipped.length > 0 ? "text-danger" : "text-muted"}>
          Skipped months: {skipped.length}
        </p>
      </section>

      {/* Decorative summary of the list below; the list is the accessible source. */}
      <div
        role="img"
        aria-label="Savings to date per month; skipped months in red"
        className="h-48 rounded-card bg-surface p-2"
      >
        <ResponsiveContainer width="100%" height="100%">
          {/* accessibilityLayer off: the month list below is the keyboard / screen-reader source. */}
          <BarChart data={months} accessibilityLayer={false}>
            <XAxis dataKey="month" tickFormatter={formatMonth} />
            <YAxis hide />
            <Bar dataKey="saved_to_date" isAnimationActive={false}>
              {months.map((month) => (
                <Cell key={month.month} className={month.skipped ? "fill-danger" : "fill-brand"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <ol aria-label="Months" className="rounded-card bg-surface px-4">
        {months.map((month) => (
          <li key={month.month} className="border-b border-line py-2">
            <div className="flex justify-between gap-4">
              <span>{formatMonth(month.month)}</span>
              {month.skipped ? (
                <strong className="text-danger">Skipped</strong>
              ) : (
                <span className="font-semibold">+{formatHuf(month.transfer)}</span>
              )}
            </div>
            <p className="text-sm text-muted">
              Saved so far: {formatHuf(month.saved_to_date)} · Balance after:{" "}
              {formatHuf(month.balance_after)}
            </p>
            {month.note !== null && <p className="text-sm text-danger">{month.note}</p>}
          </li>
        ))}
      </ol>

      <Link to={`/plans/${planId}`} className={buttonClass("secondary")}>
        Back to plan
      </Link>
    </Screen>
  );
}
```

The `fill-danger` / `fill-brand` classes set the CSS `fill` property from the tokens, which overrides Recharts' `fill` attribute, so the chart uses no hex colours.

- [ ] **Step 6: Wire the route**

In `frontend/src/App.tsx`, import `TimeMachineScreen` and add inside the `RequireLogin` route:

```tsx
        <Route path="/plans/:planId/time-machine" element={<TimeMachineScreen />} />
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass. A Recharts console warning about width/height 0 in jsdom is expected and harmless.

- [ ] **Step 8: Traceability, changelog, lint**

In `docs/traceability.md`, append to the AC4 evidence cell: `; frontend/src/screens/time-machine/TimeMachineScreen.test.tsx::test_ac4_skipped_month_is_flagged_with_backend_note`. Change its Verification cell to `automated + manual` (the chart colours are checked manually, Task 12).

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend time machine: total saved, savings chart with skipped months highlighted, month list with the backend's skipped-month notes (AC4).
```

Run: `cd frontend && npm run fmt && npm run lint && cd .. && make docs-check`. Expected: clean, `docs-check: OK`.

- [ ] **Step 9: Suggested commit (user commits)**

`feat(frontend): time machine with skipped months (AC4)`

---

### Task 10: Mandate screen and plan acceptance (AC7)

Deliverable: the mandate terms and clauses from the API; for a proposed plan, one "Sign mandate and accept plan" button that cannot fire twice and shows the 409 message when another plan is active.

**Files:**
- Create: `frontend/src/screens/mandate/MandateScreen.tsx`, `frontend/src/screens/mandate/MandateScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `docs/traceability.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `GET /api/plans/{id}/mandate` (Task 2), `usePlan`, `usePlanAction` (Task 8), `keys` (Task 5), components and `formatHuf`, `formatDay` (Task 4), `plan`, `mockApi`, `renderScreen` (Task 3).
- Produces: `useMandate(planId: number)`; `MandateScreen` at `/plans/:planId/mandate` (title "Mandate"); button "Sign mandate and accept plan"; after acceptance navigates to `/active`.

- [ ] **Step 1: Write the failing tests**

`frontend/src/screens/mandate/MandateScreen.test.tsx`:

```tsx
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { MandateOut } from "../../api/types";
import { plan } from "../../test/fixtures";
import { mockApi, renderScreen, type Reply } from "../../test/render";
import { MandateScreen } from "./MandateScreen";

const CLAUSES = [
  {
    number: 1,
    text: "SaverAI may transfer only to the products listed in this mandate, at most the monthly maximum in total per calendar month.",
  },
  { number: 2, text: "No transfer may leave the current account below the minimum balance." },
];
const PREVIEW: MandateOut = {
  status: "unsigned",
  version: null,
  signed_at: null,
  max_monthly_amount: 73_500,
  min_balance: 100_000,
  per_transfer_approval: false,
  products: [{ id: 4, name: "Balanced fund", risk_level: 3, liquid: false }],
  clauses: CLAUSES,
};
const ACCEPT = "Sign mandate and accept plan";

function start() {
  renderScreen(<MandateScreen />, { path: "/plans/:planId/mandate", url: "/plans/7/mandate" });
  return userEvent.setup();
}

test("shows the unsigned terms and clauses from the API", async () => {
  mockApi({
    "GET /api/plans/7": { body: plan() },
    "GET /api/plans/7/mandate": { body: PREVIEW },
  });
  start();
  expect(await screen.findByText(/Not signed yet/)).toBeInTheDocument();
  expect(screen.getByText("73,500 HUF")).toBeInTheDocument();
  expect(screen.getByText("100,000 HUF")).toBeInTheDocument();
  expect(screen.getByText("Balanced fund (risk 3)")).toBeInTheDocument();
  expect(screen.getByText(/§2 No transfer may leave the current account/)).toBeInTheDocument();
});

test("accepting signs the mandate and opens my plan", async () => {
  const calls = mockApi({
    "GET /api/plans/7": { body: plan() },
    "GET /api/plans/7/mandate": { body: PREVIEW },
    "POST /api/plans/7/accept": { body: plan({ status: "accepted" }) },
  });
  const user = start();
  await user.click(await screen.findByRole("button", { name: ACCEPT }));
  expect(await screen.findByText("Navigated to /active")).toBeInTheDocument();
  expect(calls.filter((call) => call.path === "/api/plans/7/accept")).toHaveLength(1);
});

test("test_ac7_accept_button_is_disabled_while_accepting", async () => {
  let release: (reply: Reply) => void = () => undefined;
  const calls = mockApi({
    "GET /api/plans/7": { body: plan() },
    "GET /api/plans/7/mandate": { body: PREVIEW },
    "POST /api/plans/7/accept": () => new Promise<Reply>((resolve) => (release = resolve)),
  });
  const user = start();
  const button = await screen.findByRole("button", { name: ACCEPT });
  await user.click(button);
  await waitFor(() => expect(button).toBeDisabled());
  await user.click(button); // a second tap while the first request is in flight
  expect(calls.filter((call) => call.path === "/api/plans/7/accept")).toHaveLength(1);

  release({ body: plan({ status: "accepted" }) });
  expect(await screen.findByText("Navigated to /active")).toBeInTheDocument();
});

test("shows the conflict message when another plan is active", async () => {
  mockApi({
    "GET /api/plans/7": { body: plan() },
    "GET /api/plans/7/mandate": { body: PREVIEW },
    "POST /api/plans/7/accept": {
      status: 409,
      body: { detail: "Pause your active plan before accepting a new one." },
    },
  });
  const user = start();
  await user.click(await screen.findByRole("button", { name: ACCEPT }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Pause your active plan");
  expect(screen.queryByText(/Navigated to/)).toBeNull();
});

test("a signed mandate shows its version and no accept button", async () => {
  mockApi({
    "GET /api/plans/7": { body: plan({ status: "accepted" }) },
    "GET /api/plans/7/mandate": {
      body: { ...PREVIEW, status: "active", version: 2, signed_at: "2026-10-06T12:00:00Z" },
    },
  });
  start();
  expect(await screen.findByText("Version 2, signed 2026-10-06 (active)")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: ACCEPT })).toBeNull();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/screens/mandate`
Expected: FAIL with `Failed to resolve import "./MandateScreen"`.

- [ ] **Step 3: Add the hook**

Append to `frontend/src/api/hooks.ts` (add `MandateOut` to the `./types` import):

```ts
export function useMandate(planId: number) {
  return useQuery({
    queryKey: keys.mandate(planId),
    queryFn: () => apiFetch<MandateOut>(`/api/plans/${planId}/mandate`),
  });
}
```

- [ ] **Step 4: Implement the screen**

`frontend/src/screens/mandate/MandateScreen.tsx`:

```tsx
import { Link, useNavigate, useParams } from "react-router";
import { useMandate, usePlan, usePlanAction } from "../../api/hooks";
import { Button, buttonClass } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Screen } from "../../components/Screen";
import { formatDay, formatHuf } from "../../format";

/** Mandate terms and clauses. Accepting a proposed plan signs the next mandate version. */
export function MandateScreen() {
  const planId = Number(useParams().planId);
  const mandate = useMandate(planId);
  const plan = usePlan(planId);
  const accept = usePlanAction("accept");
  const navigate = useNavigate();

  if (!mandate.isSuccess || !plan.isSuccess) {
    const error = mandate.error ?? plan.error;
    return (
      <Screen title="Mandate">{error ? <ErrorMessage error={error} /> : <p>Loading…</p>}</Screen>
    );
  }
  const terms = mandate.data;

  return (
    <Screen title="Mandate">
      <p>
        {terms.status === "unsigned"
          ? "Not signed yet. Accepting the plan signs this mandate."
          : `Version ${terms.version ?? ""}, signed ${formatDay(terms.signed_at ?? "")} (${terms.status})`}
      </p>

      <dl className="space-y-2 rounded-card bg-surface p-4">
        <div className="flex justify-between gap-4">
          <dt>Maximum per month</dt>
          <dd className="font-semibold">{formatHuf(terms.max_monthly_amount)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt>Minimum balance kept</dt>
          <dd className="font-semibold">{formatHuf(terms.min_balance)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt>Approval for each transfer</dt>
          <dd className="font-semibold">{terms.per_transfer_approval ? "Yes" : "No"}</dd>
        </div>
      </dl>

      <section>
        <h2 className="mb-2 text-lg font-semibold">Allowed products</h2>
        <ul className="list-disc pl-6">
          {terms.products.map((product) => (
            <li key={product.id}>
              {product.name} (risk {product.risk_level})
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-2 text-lg font-semibold">Clauses</h2>
        <ol className="space-y-2">
          {terms.clauses.map((clause) => (
            <li key={clause.number}>
              §{clause.number} {clause.text}
            </li>
          ))}
        </ol>
      </section>

      <ErrorMessage error={accept.error} />
      {plan.data.status === "proposed" && (
        <Button
          className="w-full"
          disabled={accept.isPending}
          onClick={() => accept.mutate(planId, { onSuccess: () => navigate("/active") })}
        >
          Sign mandate and accept plan
        </Button>
      )}
      <Link to={`/plans/${planId}`} className={buttonClass("secondary")}>
        Back to plan
      </Link>
    </Screen>
  );
}
```

`getByText("Balanced fund (risk 3)")` matches the `<li>`'s joined text. If a test cannot find a joined string, render it as one template string instead of changing the test.

- [ ] **Step 5: Wire the route**

In `frontend/src/App.tsx`, import `MandateScreen` and add inside the `RequireLogin` route:

```tsx
        <Route path="/plans/:planId/mandate" element={<MandateScreen />} />
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass (5 mandate tests).

- [ ] **Step 7: Traceability, changelog, lint**

In `docs/traceability.md`, append to the AC7 evidence cell: `; frontend/src/screens/mandate/MandateScreen.test.tsx::test_ac7_accept_button_is_disabled_while_accepting`.

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend mandate screen: limits, allowed products and clauses from the API; one-tap "Sign mandate and accept plan" that cannot submit twice (AC7) and shows the conflict when another plan is active.
```

Run: `cd frontend && npm run fmt && npm run lint && cd .. && make docs-check`. Expected: clean, `docs-check: OK`.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): mandate screen and plan acceptance (AC7)`

---

### Task 11: Active plan screen: pause and transfer approval (AC6)

Deliverable: "My plan" shows the accepted or paused plan, lets the customer pause it, lists monthly transfers with mandate version and clause, and approves transfers that wait for approval (low confidence, AC6). With no plan it shows an empty state.

**Files:**
- Create: `frontend/src/screens/active-plan/ActivePlanScreen.tsx`, `frontend/src/screens/active-plan/ActivePlanScreen.test.tsx`
- Modify: `frontend/src/api/hooks.ts`, `frontend/src/App.tsx`, `docs/traceability.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: `GET /api/plans/active`, `POST /api/plans/{id}/pause`, `GET /api/executions`, `POST /api/executions/{id}/approve` (backend Task 13), `useActivePlan` (Task 6), `usePlanAction` (Task 8), `PlanItemList` (Task 8), components and `formatHuf`, `formatMonth` (Task 4).
- Produces: `useExecutions()` (data `ExecutionOut[]`), `useApproveExecution()` (mutate `executionId: number`); `ActivePlanScreen` at `/active` (title "My plan"); status text "Active" / "Paused"; approve buttons labelled `Approve transfer of <amount> for <YYYY-MM>`.

- [ ] **Step 1: Write the failing tests**

`frontend/src/screens/active-plan/ActivePlanScreen.test.tsx`:

```tsx
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import type { ExecutionOut, PlanOut } from "../../api/types";
import { plan } from "../../test/fixtures";
import { mockApi, renderScreen } from "../../test/render";
import { ActivePlanScreen } from "./ActivePlanScreen";

const WAITING: ExecutionOut = {
  id: 31,
  period: "2026-10-01",
  status: "awaiting_approval",
  amount: 55_000,
  mandate_version: 1,
  clause: 3,
  reason: "Per-transfer approval is required.",
};

function start() {
  renderScreen(<ActivePlanScreen />, { path: "/active" });
  return userEvent.setup();
}

test("shows the empty state when there is no active plan", async () => {
  mockApi({
    "GET /api/plans/active": { status: 404, body: { detail: "No active plan." } },
    "GET /api/executions": { body: [] },
  });
  start();
  expect(await screen.findByText("You have no active plan.")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Start a savings plan" })).toHaveAttribute(
    "href",
    "/questionnaire",
  );
  expect(screen.queryByRole("alert")).toBeNull();
});

test("pausing sends the request and shows the paused state", async () => {
  let current: PlanOut = plan({ status: "accepted" });
  const calls = mockApi({
    "GET /api/plans/active": () => ({ body: current }),
    "GET /api/executions": { body: [] },
    "POST /api/plans/7/pause": () => {
      current = plan({ status: "paused" });
      return { body: current };
    },
  });
  const user = start();
  expect(await screen.findByText("Active", { exact: true })).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Pause plan" }));

  expect(await screen.findByText("Paused", { exact: true })).toBeInTheDocument();
  expect(screen.getByText("No transfers run while the plan is paused.")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Pause plan" })).toBeNull();
  expect(calls.filter((call) => call.path === "/api/plans/7/pause")).toHaveLength(1);
});

test("test_ac6_waiting_transfer_can_be_approved", async () => {
  let executions: ExecutionOut[] = [WAITING];
  const calls = mockApi({
    "GET /api/plans/active": {
      body: plan({ status: "accepted", confidence: "low", per_transfer_approval: true }),
    },
    "GET /api/executions": () => ({ body: executions }),
    "POST /api/executions/31/approve": () => {
      executions = [{ ...WAITING, status: "executed", clause: 1, reason: "Within the mandate." }];
      return { body: executions[0] };
    },
  });
  const user = start();
  expect(await screen.findByText("Waiting for your approval")).toBeInTheDocument();
  expect(screen.getByText(/mandate v1, clause 3/)).toBeInTheDocument();
  await user.click(
    screen.getByRole("button", { name: "Approve transfer of 55,000 HUF for 2026-10" }),
  );

  expect(await screen.findByText("Executed")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Approve transfer/ })).toBeNull();
  expect(calls.filter((call) => call.path === "/api/executions/31/approve")).toHaveLength(1);
});

test("an already handled transfer shows the conflict message", async () => {
  mockApi({
    "GET /api/plans/active": { body: plan({ status: "accepted" }) },
    "GET /api/executions": { body: [WAITING] },
    "POST /api/executions/31/approve": {
      status: 409,
      body: { detail: "This transfer is not waiting for approval." },
    },
  });
  const user = start();
  await user.click(await screen.findByRole("button", { name: /Approve transfer/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent("not waiting for approval");
});

test("says when no transfer has run yet", async () => {
  mockApi({
    "GET /api/plans/active": { body: plan({ status: "accepted" }) },
    "GET /api/executions": { body: [] },
  });
  start();
  expect(await screen.findByText(/No transfers yet/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "View mandate" })).toHaveAttribute(
    "href",
    "/plans/7/mandate",
  );
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx vitest run src/screens/active-plan`
Expected: FAIL with `Failed to resolve import "./ActivePlanScreen"`.

- [ ] **Step 3: Add the hooks**

Append to `frontend/src/api/hooks.ts` (add `ExecutionOut` to the `./types` import):

```ts
export function useExecutions() {
  return useQuery({
    queryKey: keys.executions,
    queryFn: () => apiFetch<ExecutionOut[]>("/api/executions"),
  });
}

/** Approve one transfer that waits for approval (low confidence, mandate clause 3 — AC6). */
export function useApproveExecution() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (executionId: number) =>
      apiFetch<ExecutionOut>(`/api/executions/${executionId}/approve`, { method: "POST" }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: keys.executions });
    },
  });
}
```

- [ ] **Step 4: Implement the screen**

`frontend/src/screens/active-plan/ActivePlanScreen.tsx`:

```tsx
import { Link } from "react-router";
import {
  useActivePlan,
  useApproveExecution,
  useExecutions,
  usePlanAction,
} from "../../api/hooks";
import type { ExecutionStatus } from "../../api/types";
import { Button, buttonClass } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { PlanItemList } from "../../components/PlanItemList";
import { Screen } from "../../components/Screen";
import { formatHuf, formatMonth } from "../../format";

const EXECUTION_LABEL: Record<ExecutionStatus, string> = {
  executed: "Executed",
  denied: "Denied",
  awaiting_approval: "Waiting for your approval",
};

export function ActivePlanScreen() {
  const active = useActivePlan();
  const executions = useExecutions();
  const pause = usePlanAction("pause");
  const approve = useApproveExecution();

  if (!active.isSuccess) {
    return (
      <Screen title="My plan">
        {active.isError ? <ErrorMessage error={active.error} /> : <p>Loading…</p>}
      </Screen>
    );
  }
  const plan = active.data;
  if (plan === null) {
    return (
      <Screen title="My plan">
        <p>You have no active plan.</p>
        <Link to="/questionnaire" className={buttonClass("primary")}>
          Start a savings plan
        </Link>
      </Screen>
    );
  }

  return (
    <Screen title="My plan">
      <section className="rounded-card bg-surface p-4">
        <p>
          Status: <strong>{plan.status === "paused" ? "Paused" : "Active"}</strong>
        </p>
        <p className="text-3xl font-bold">{formatHuf(plan.monthly_amount)}</p>
        <p className="text-muted">per month</p>
        {plan.status === "paused" && <p>No transfers run while the plan is paused.</p>}
      </section>

      <PlanItemList items={plan.items} />
      <Link to={`/plans/${plan.id}/mandate`} className={buttonClass("secondary")}>
        View mandate
      </Link>
      {plan.status === "accepted" && (
        <Button variant="danger" disabled={pause.isPending} onClick={() => pause.mutate(plan.id)}>
          Pause plan
        </Button>
      )}
      <ErrorMessage error={pause.error ?? approve.error} />

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Transfers</h2>
        <ErrorMessage error={executions.error} />
        {executions.isSuccess && executions.data.length === 0 && (
          <p className="text-muted">No transfers yet. Transfers run once a month.</p>
        )}
        <ul className="space-y-2">
          {executions.data?.map((execution) => (
            <li key={execution.id} className="space-y-1 rounded-card border border-line bg-surface p-3">
              <div className="flex justify-between gap-4">
                <span>{formatMonth(execution.period)}</span>
                <span className="font-semibold">{formatHuf(execution.amount)}</span>
              </div>
              <p>{EXECUTION_LABEL[execution.status]}</p>
              <p className="text-sm text-muted">
                {execution.reason} (mandate v{execution.mandate_version}, clause {execution.clause})
              </p>
              {execution.status === "awaiting_approval" && (
                <Button
                  disabled={approve.isPending}
                  aria-label={`Approve transfer of ${formatHuf(execution.amount)} for ${formatMonth(execution.period)}`}
                  onClick={() => approve.mutate(execution.id)}
                >
                  Approve
                </Button>
              )}
            </li>
          ))}
        </ul>
      </section>
    </Screen>
  );
}
```

- [ ] **Step 5: Wire the route**

In `frontend/src/App.tsx`, import `ActivePlanScreen` and add inside the `RequireLogin` route:

```tsx
        <Route path="/active" element={<ActivePlanScreen />} />
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx vitest run`
Expected: all pass (5 active plan tests).

- [ ] **Step 7: Traceability, changelog, lint**

In `docs/traceability.md`, append to the AC6 evidence cell: `; frontend/src/screens/active-plan/ActivePlanScreen.test.tsx::test_ac6_waiting_transfer_can_be_approved`.

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Frontend "My plan": active or paused plan, pause, monthly transfers with mandate version and clause, approval of transfers that wait for the customer (AC6).
```

Run: `cd frontend && npm run fmt && npm run lint && cd .. && make docs-check`. Expected: clean, `docs-check: OK`.

- [ ] **Step 8: Suggested commit (user commits)**

`feat(frontend): active plan with pause and transfer approval (AC6)`

---

### Task 12: Playwright e2e, manual checks, architecture, AI usage draft, final verification

Deliverable: one Playwright run of the main workflow (questionnaire → plan → time machine → mandate → accept) plus the AC5 path, with 44 px touch-target checks on every screen; updated docs; a clean `make check` and `make e2e` from a fresh database.

**Files:**
- Create: `frontend/playwright.config.ts`, `frontend/e2e/global-setup.ts`, `frontend/e2e/main-flow.spec.ts`
- Modify: `docs/manual-checks.md`, `docs/architecture.md`, `docs/ai-usage.md`, `docs/traceability.md`, `README.md`, `CHANGELOG.md`

**Interfaces:**
- Consumes: the whole backend plan (`make seed` personas anna / bence with `SEED_PASSWORD`, `manage.py flush|migrate|seed|run_orders`), every screen from Tasks 5–11 and their labels.
- Produces: `make e2e` green; e2e test titles `test_ac7_main_flow_questionnaire_plan_time_machine_accept`, `test_ac5_customer_without_surplus_gets_explanation`.

- [ ] **Step 1: Write the Playwright config and the database reset**

`frontend/playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  workers: 1, // one shared SQLite database
  use: {
    ...devices["Pixel 7"], // mobile banking UI
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
 * Fresh demo data for every run: anna's plan from an earlier run would make "accept" a 409.
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

async function login(page: Page, username: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(process.env.SEED_PASSWORD ?? "");
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();
}

/** AGENTS.md section 7: every visible interactive element is at least 44 px tall. */
async function expectTouchTargets(page: Page): Promise<void> {
  const targets = page.locator("button, a, input:not([type=radio]), label:has(input[type=radio])");
  for (const target of await targets.all()) {
    if (!(await target.isVisible())) continue;
    const box = await target.boundingBox();
    const name = await target.evaluate((element) => element.outerHTML.slice(0, 80));
    expect(box?.height ?? 0, name).toBeGreaterThanOrEqual(44);
  }
}

async function answerQuestionnaire(page: Page, fund: string): Promise<void> {
  await page.getByRole("link", { name: "New plan" }).click();
  await page.getByLabel("3 – Balanced").check();
  await page.getByLabel("Existing emergency fund (HUF)").fill(fund);
  await expectTouchTargets(page);
  await page.getByRole("button", { name: "Show my plan" }).click();
}

test("test_ac7_main_flow_questionnaire_plan_time_machine_accept", async ({ page }) => {
  await login(page, "anna");
  await expectTouchTargets(page);

  await answerQuestionnaire(page, "750000");
  await expect(page.getByRole("heading", { name: "Your plan" })).toBeVisible();
  await expect(page.getByText("73,500 HUF").first()).toBeVisible(); // AC1
  await expectTouchTargets(page);

  await page.getByRole("link", { name: "Replay on my history (time machine)" }).click();
  await expect(page.getByRole("heading", { name: "Time machine" })).toBeVisible();
  await expect(page.getByRole("list", { name: "Months" }).getByRole("listitem").first()).toBeVisible();
  await expectTouchTargets(page);

  await page.getByRole("link", { name: "Back to plan" }).click();
  await page.getByRole("link", { name: "Review mandate and accept" }).click();
  await expect(page.getByText("Not signed yet", { exact: false })).toBeVisible();
  await expectTouchTargets(page);

  await page.getByRole("button", { name: "Sign mandate and accept plan" }).click();
  await expect(page.getByRole("heading", { name: "My plan" })).toBeVisible();
  await expect(page.getByText("Active", { exact: true })).toBeVisible();
  await expectTouchTargets(page);

  // AC7: the accepted plan's mandate is now signed (version 1); going back offers no second accept.
  await page.getByRole("link", { name: "View mandate" }).click();
  await expect(page.getByText(/Version 1, signed/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign mandate and accept plan" })).toHaveCount(0);
});

test("test_ac5_customer_without_surplus_gets_explanation", async ({ page }) => {
  await login(page, "bence");
  await answerQuestionnaire(page, "0");
  await expect(page.getByRole("status")).toContainText("no surplus");
  await expect(page.getByRole("heading", { name: "New plan" })).toBeVisible();
});
```

- [ ] **Step 3: Run e2e**

Run: `make e2e`
Expected: the global setup prints migrations, flush and `Seeded 5 products and 4 personas.`, then `2 passed`.
If a touch-target assertion fails, the message names the element's HTML: fix the component's classes (`min-h-touch`, `buttonClass`), not the test. If `.env` has no `SEED_PASSWORD`, the setup stops with a clear message.

Run it a second time: `make e2e`. Expected: `2 passed` again (the reset makes it repeatable).

- [ ] **Step 4: Manual checks**

Append to `docs/manual-checks.md`:

````markdown
## Frontend setup
`make setup && make migrate && make seed && make dev`, with `SAVERAI_FIXED_DATE=2026-10-06` in `.env`.
Open http://localhost:5173 on a phone-sized window (browser dev tools, 390 × 844).

## AC4 — time machine colours (UI)
1. In Django admin (http://localhost:8000/admin/), set anna's account balance to 300000.
2. Log in as `anna` in the app → New plan → risk 3, emergency fund 750000 → Show my plan →
   "Replay on my history (time machine)".
Expected: skipped months have red bars in the chart, "Skipped" in red in the list and the note
"…the transfer was skipped because it would have left less than 100,000 HUF on your account."
"Skipped months: N" is red when N > 0.

## AC6 — approving a transfer (UI)
1. Log in as `dani` → New plan → risk 3, emergency fund 0 → Show my plan.
Expected: "Confidence: Low" and "Every transfer needs your approval."
2. "Review mandate and accept" → "Sign mandate and accept plan".
3. In a terminal: `cd backend && uv run python manage.py run_orders`.
4. Reload "My plan".
Expected: the transfer shows "Waiting for your approval (mandate v1, clause 3)". Press "Approve".
Expected: it changes to "Executed".

## Keyboard and screen reader basics
1. On every screen, press Tab through all controls.
Expected: every control gets a visible focus outline; the order follows the screen top to bottom;
every button and field announces a name (VoiceOver: Cmd+F5 on macOS).

## RuleConfig change in the UI (defence rehearsal)
1. Django admin → Rule configuration → "Monthly share percent" = 60 → Save.
2. Log in as `anna` → New plan → risk 3, emergency fund 750000 → Show my plan.
Expected: 63,000 HUF and the explanation says 60%. Set it back to 70.
````

- [ ] **Step 5: Architecture, README, traceability**

Append to `docs/architecture.md`:

````markdown
## Frontend
React SPA in `frontend/` (ADR-0003). Screens in `src/screens/<name>/`, shared UI in
`src/components/`, design tokens in `src/theme/theme.css`.

```
screen → hook (src/api/hooks.ts, TanStack Query) → apiFetch (src/api/client.ts) → /api (Vite proxy) → Django Ninja
```

- The frontend computes no money and makes no rule decision; it formats API values
  (`src/format.ts`) and renders backend explanation texts verbatim.
- Auth: Django session cookie. `apiFetch` sends `X-CSRFToken` from the `csrftoken` cookie on every
  unsafe request (the token rotates on login). Any 401 clears the cached user and the router sends
  the customer to `/login`.
- Routes: `/login`, `/`, `/questionnaire`, `/plans/:planId`, `/plans/:planId/time-machine`,
  `/plans/:planId/mandate`, `/active`.
````

Add to `README.md` a section:

```markdown
## Using the app
After `make seed` and `make dev`, open http://localhost:5173 and log in as a demo persona
(password: `SEED_PASSWORD` from `.env`). Admin users use Django admin at http://localhost:8000/admin/.
```

In `docs/traceability.md`, append to the evidence cells:
- AC1: `; frontend/e2e/main-flow.spec.ts::test_ac7_main_flow_questionnaire_plan_time_machine_accept`
- AC5: `; frontend/e2e/main-flow.spec.ts::test_ac5_customer_without_surplus_gets_explanation`
- AC7: `; frontend/e2e/main-flow.spec.ts::test_ac7_main_flow_questionnaire_plan_time_machine_accept`
- AC6: change Verification to `automated + manual` and append `; manual steps in docs/manual-checks.md#ac6--approving-a-transfer-ui`

- [ ] **Step 6: Draft the AI usage entry**

Append to `docs/ai-usage.md` (the human author verifies and completes the decision fields):

```markdown
### Case 3 — Frontend test strategy (DRAFT, author to complete)
- Phase: testing
- Tool and model: Claude Code, Claude Opus 5.5 (superpowers "writing-plans" skill)
- Problem: decide how to test a React UI whose every number comes from the backend, so tests are
  fast, deterministic and still prove AC4–AC8 from the customer's side.
- Context given and key instruction: `docs/specification.md`, `docs/tasks.md`, `AGENTS.md`, the
  backend plan's API contract; "Create a similar plan for the frontend based on the specification
  and to do list".
- Essence of the AI suggestion: Vitest + Testing Library with a 25-line `fetch` stub instead of
  MSW; AC tests named `test_acN_...` and checked by `make docs-check`; AC4 asserted on the month
  list, not the chart SVG (jsdom has no layout); one Playwright main-flow test on a mobile viewport
  that resets the database and measures 44 px touch targets; two new read endpoints so the UI never
  hard-codes 100,000 HUF or the mandate clauses.
- Decision (accepted / modified / rejected) and technical reasons: TODO author
- Verification: `make check` (Vitest), `make e2e` (Playwright), `docs/traceability.md`.
- Limitations of this verification: component tests use a stubbed API, so contract drift between
  `src/api/types.ts` and `backend/api/schemas.py` is caught only by the e2e test; jsdom cannot
  check layout or colour contrast (manual checks cover those).
```

- [ ] **Step 7: Changelog**

Add to `CHANGELOG.md` under `### Added`:

```markdown
- Playwright e2e of the main workflow (questionnaire → plan → time machine → mandate → accept) and the no-surplus path on a mobile viewport, with 44 px touch-target checks (AC1, AC5, AC7).
- Frontend manual checks and architecture section; AI usage Case 3 draft.
```

- [ ] **Step 8: Final verification from a clean state**

Run:

```bash
rm -rf frontend/node_modules
make setup
make check
make e2e
cd frontend && npm run build
```

Expected: `make check` — backend lint and tests green, `tsc`/ESLint/Prettier clean, all Vitest tests pass, `docs-check: OK`; `make e2e` — `2 passed`; Vite build succeeds.

In `docs/traceability.md`, update the "Last full run" line under the table with the date and the backend, Vitest and Playwright counts from this output.

- [ ] **Step 9: Suggested commit (user commits)**

`test(e2e): main workflow playwright test, manual checks and frontend docs`

After the user commits: tag `v1.0-first-version` (AGENTS.md section 8.5) is the user's step and is out of scope for this plan.
