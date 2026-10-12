# Dual implementation — Time machine screen (Figma 06, AC4)

Homework requirement: implement one requirement twice with two separate AI tools and compare the
results (`docs/Homework_requirements_EN.pdf`, "Documenting the use of AI"; AGENTS.md section 11).

## 1. Setup

| | Claude | Gemini |
| --- | --- | --- |
| Tool | Claude Code (terminal agent) | Google Antigravity (IDE agent) |
| Model | Claude Sonnet 5.5 | Gemini 3.8 Flash |
| Branch | `dual/claude` (`ab4f64b`) | `dual/gemini` (`f9dd2f9`) |
| Base | `dual/base` = `main` at `a09afc2` | same |
| Commit time | 2026-10-11 18:39 | 2026-10-11 18:51 |
| Wall-clock time (author's measurement) | ~6 min | ~12 min |
| Weekly usage limit consumed (author's measurement) | ~2 % | ~20 % |

**Feature:** `TimeMachineScreen` at `/plans/:planId/time-machine`, Task 15 of
`docs/superpowers/plans/2026-10-10-frontend-figma-implementation.md`. The screen is read-only and maps to
AC4. It shows stat tiles, the saved-to-date chart with skipped months, a month table, the backend notes
for skipped months and "Continue to mandate". All prerequisites (Tasks 1–14: hooks, `SavedChart`,
tokens, layout components, fixtures) were already on the base, so both tools started from the same
code and the same instructions (`AGENTS.md`; `CLAUDE.md` and `GEMINI.md` are symlinks to it).

### Implementation prompt (identical for both tools)

```markdown
Implement the SaverAI time machine screen (AC4). This same prompt goes to two AI tools for comparison; work alone.

Read: AGENTS.md, AC4 in docs/specification.md, existing code in frontend/src (hooks, components, format, theme).
Design: Figma QUT5rnXj1U6BYjty7YH5uS, frame 7:452 (06 Financial time machine) and notes frame 10:1074.

Build `frontend/src/screens/time-machine/TimeMachineScreen.tsx` at `/plans/:planId/time-machine` (add the route in App.tsx):
stat tiles (saved, transfers made, months skipped), SavedChart with skipped months marked, month-by-month table,
skipped-months list with each backend `note` shown verbatim, "Continue to mandate" only for proposed plans.
Reuse existing components; do not change shared code.

Done when:
- frozen test `TimeMachineScreen.test.tsx` passes unchanged (never edit it); `make check` is green
- no money/date computation in the frontend, token-only styling, 44 px targets, works at 375 px
- traceability.md and CHANGELOG.md updated

Commit on your branch, then report: files changed, test results, design decisions, how you checked the result against Figma.
```

### Evaluation prompt (used to produce this report, Claude Code, Claude Opus 5.5)

```markdown
Compare branches dual/claude and dual/gemini (both from dual/base, prompt in docs/dual-prompt.md).
Write docs/dual-implementation.md:
1. Results: run the tests, lint, tsc and `make check` on each branch yourself; diff stat; whether any test or shared code changed.
2. Rule compliance (AGENTS.md), citing file:line.
3. Visual match with Figma frame 7:452 at 1440 px and 375 px, with screenshots.
4. Code differences and edge cases (no skipped months, accepted plan, error state).
5. Working method, from my notes: turns, manual fixes, how each tool verified its work.
6. Which branch to merge, why, and the limitations of this comparison.
Back every claim with output, a screenshot or file:line.
```

Neither prompt was committed as `docs/dual-prompt.md`; both are recorded here instead.

## 2. Important caveat: the base was not clean

The plan file on `dual/base` still contained the finished reference code for Task 15
(`docs/superpowers/plans/2026-10-10-frontend-figma-implementation.md`, Step 1 test at about line 6297,
Step 3 screen at line 6352). The plan had been written earlier with Claude Code (Opus 5.5). The planned
step "remove Task 15 Step 3 from the plan on `dual/base`" was not done, and the frozen test file named
in the prompt was not committed on the base either.

Consequences, measured with `diff -w` after running prettier on the plan's code block:

- **Gemini's screen differs from the plan's reference code by 3 lines:** it adds an
  `<div className="overflow-x-auto">` wrapper around the table and wraps `{m.note}` in a `<span>`.
  Gemini's test file is the plan's Step 1 test, unchanged apart from prettier formatting.
- **Claude's screen differs from the reference by about 200 changed lines.** It has its own structure
  (`Legend`, `MonthRow`, `MonthTable`, `SkippedMonths`) and its own test file.

So the Gemini branch mostly shows that Gemini **found and reused the reference solution in the
repository**. It is not a measure of how well Gemini designs a screen from Figma. The Claude branch is an
independent implementation. The comparison below is still valid as a comparison of *working methods*,
but not as a like-for-like comparison of code-generation quality.

## 3. Objective results

All commands were run by the evaluator on each branch (2026-10-11), not taken from the tools' reports.

| Check | `dual/claude` | `dual/gemini` |
| --- | --- | --- |
| `npx vitest run` (whole frontend) | 12 files, **78 passed** | 12 files, **79 passed** |
| `npm run lint` (eslint + `tsc` + prettier) | clean | clean |
| `python3 scripts/docs_check.py` | OK | OK |
| Files changed vs base | 5 (+234 / −1) | 5 (+184 / −1) |
| Screen size | 186 lines | 128 lines |
| Own tests | 3, in `TimeMachineView.test.tsx` | 4, in `TimeMachineScreen.test.tsx` (= plan's test) |
| Shared components, hooks, fixtures changed | no | no |
| Existing tests changed | no | no |
| `traceability.md` AC4 row and `CHANGELOG.md` | updated | updated |

The backend is unchanged on both branches, so the backend part of `make check` was not re-run.

**Cross-run.** Each branch's tests were run against the other branch's screen, with the test file copied
in temporarily:

| Tests | on Claude's screen | on Gemini's screen |
| --- | --- | --- |
| Gemini's tests (= plan's Step 1 tests) | **1 passed, 3 failed** | 4 passed |
| Claude's tests | 3 passed | **3 passed** |

The three failures are accessible-name contract mismatches, not wrong behaviour:

- `Unable to find role="region" and name "Totals"`: Claude's stat-tile grid is a plain `<div>`
  without `aria-label="Totals"`.
- `Unable to find role="table" and name "Saved to date, month by month"`: Claude's table caption is
  "Month by month replay of the plan".
- Claude's skipped-months `<ul>` has no `aria-label`.

The plan's later e2e step (Task 18, plan line 7618–7620) uses the same names. It clicks
"See month by month" and expects the table "Saved to date, month by month". Claude's screen would need
these names before Task 18.

## 4. Rule compliance (AGENTS.md)

| Rule | Claude | Gemini |
| --- | --- | --- |
| No money/date computation in the frontend | OK: only `formatHuf`/`formatMonth`; `filter` on `skipped` is not money arithmetic | OK, same |
| Backend `note` verbatim (golden rule 2) | OK (`SkippedMonths`, `<span>{m.note}</span>`) | OK |
| Token-only styling | OK: `bg-chart-saved`, `bg-chart-income`, `border-chart-skipped`, `text-h2` exist in `src/theme/theme.css` (lines 32–34, 60) | OK |
| No `any` / no `!` | OK; the test has one `as HTMLElement` cast | OK |
| Prompt: test file name `TimeMachineScreen.test.tsx` | not followed (`TimeMachineView.test.tsx`) | followed |
| Prompt: "work alone" | followed | asked to inspect Claude's branch (refused by the author, see section 6) |
| Prompt: commit on the given branch | followed | first worked on its own branch `implement_time_machine_screen` in an Antigravity worktree (`~/.gemini/antigravity/worktrees/…`); the author had to redirect it |

## 5. Comparison with Figma frame 7:452 (code review)

Both branches were reviewed in code against a screenshot of frame `7:452` taken through the Figma MCP. **No
rendered screenshots of the two branches were taken**, so this is a code-to-design review, not a pixel
comparison (see section 8).

| Figma element | Claude | Gemini |
| --- | --- | --- |
| Header text, 3 stat tiles with captions | match | match |
| "Months skipped" caption "2025-12 and 2026-07" | `Intl.ListFormat` ("a, b, and c" for 3 months) | `join(" and ")` ("a and b and c" for 3 months) |
| Chart card title + legend "Saved to date" / "Skipped: no transfer, total unchanged" | **legend present**, in the card header as in Figma | **no legend** |
| "Value labels appear on hover…" caption | present | present |
| Month table (not visible in the Figma frame) | separate always-visible card; extra `balance_after` column | collapsed in `<details>` "See month by month" (closer to Figma) |
| 375 px table | hides 2 columns below `md`, no horizontal scroll | 5 columns in `overflow-x-auto` (scrolls inside the card) |
| Skipped months card with count badge, warning rows | match (`text-h2`) | match (`text-h3`) |
| "Continue to mandate" bottom right | match | match |

Edge cases:

| Case | Claude | Gemini |
| --- | --- | --- |
| No skipped month | card stays, text "No transfer would have been skipped." | card hidden; tile caption "None" |
| Accepted plan | no continue link (tested) | no continue link (tested) |
| Plan request fails, time machine succeeds | replay still shown, captions omitted | whole content hidden (`data && plan.data`) |
| Both requests fail | two `ErrorMessage`s (can show the same message twice) | one `ErrorMessage` (`machine.error ?? plan.error`) |
| Time machine fails, plan is proposed | continue link still shown (outside the data guard) | nothing shown |

## 6. Working method

| | Claude Code (Sonnet 5.5) | Antigravity (Gemini 3.8 Flash) |
| --- | --- | --- |
| Time / usage | ~6 min, ~2 % of the weekly limit | ~12 min, ~20 % of the weekly limit |
| Branch discipline | worked and committed on `dual/claude` | did not follow the branch at first: created `implement_time_machine_screen` in its own worktree, and the author had to redirect it to `dual/gemini` |
| Isolation | did not look at other branches | **asked to check the changes Claude had made** (Claude's branch was committed 12 minutes earlier); the author **refused** to keep the two implementations independent |
| Source of the solution | composed the screen from existing components, the Figma frame and the spec; wrote its own tests | reused the reference code and tests from the plan file almost verbatim |
| Prompt adherence | missed the test file name; did not reproduce the plan's accessible names | followed file names and the plan's test contract |
| Commit | Conventional Commit with `Co-Authored-By: Claude Sonnet 5.5` | Conventional Commit, no AI attribution trailer |

The usage percentages are relative to two different subscriptions with different quotas, so they show
how heavy each run felt on the author's plan, not comparable costs.

## 7. Decision

merge `dual/claude`, with a small follow-up commit before Task 18.

Technical reasons:

- It is the only independent implementation. The Gemini branch is essentially the plan's reference code,
  which was itself written by Claude Opus, so merging it would not add anything the plan did not already
  contain.
- It is closer to Figma: it has the chart legend, and the 375 px table has no horizontal scroll.
- It handles the "no skipped month" case explicitly, and still shows the replay when only the plan
  request fails.
- The run took half the time and much less quota, and it stayed on the assigned branch without
  intervention.

What to take from Gemini / the plan, in the follow-up commit:

- `aria-label="Totals"` on the stat-tile grid, table caption "Saved to date, month by month" and
  `aria-label="Skipped months"` on the list, so the plan's tests and the Task 18 e2e step pass.
- Optionally put the table in `<details>` "See month by month", which is closer to Figma and is what
  the e2e step clicks.
- Rename `TimeMachineView.test.tsx` to `TimeMachineScreen.test.tsx` and update `docs/traceability.md`.
- A single `ErrorMessage` (`machine.error ?? plan.error`) to avoid a duplicated error.

`dual/gemini` stays on its branch, unmerged.

## 8. Limitations

- **Contaminated base (section 2).** The reference solution was readable in the repository, and no
  frozen shared test was committed on the base. The comparison of code quality is therefore one-sided.
- One run per tool; another run or a slightly different prompt could give different results.
- Both tools read the same `AGENTS.md`, which pushes both towards the same conventions.
- Visual fidelity was reviewed in code against the Figma screenshot. Neither branch was rendered at
  1440 px or 375 px.
- Time and quota figures are the author's own measurements on different subscriptions.
