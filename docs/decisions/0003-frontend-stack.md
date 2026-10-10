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
