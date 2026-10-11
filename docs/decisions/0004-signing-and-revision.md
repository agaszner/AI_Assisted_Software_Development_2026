# 0004. Password-confirmed signing and plan revision
Date: 2026-10-11 · Status: accepted

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
