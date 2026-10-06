# SaverAI – Homework Specification

Gaszner Ádám László, BIA823

## Objective and architecture

SaverAI is a savings assistant for bank customers. The customer fills in a short questionnaire (goals, risk tolerance, planned large expenses), the app analyses past transactions to estimate the typical monthly surplus, recommends a savings and investment plan matching the answers and, once accepted, sets up recurring orders automatically. Before acceptance, a financial time machine replays the plan on the customer's last 12 months of real transactions, every plan shows a confidence level, and orders run only under a signed, versioned mandate of limits.

The application contains no AI service: all amounts, product choices, limits and explanations come from a deterministic rule engine, explanations are fixed templates filled with its results. Backend: Python/Django (rule engine, users, plans, simulated bank data). Frontend: React mobile banking UI (home, questionnaire, plan review, time machine, mandate, active plan). Transactions, products and order execution are simulated.

## Roles and main scenarios

- Customer: logs in, completes the questionnaire, accepts, rejects or edits a plan, pauses an active plan.
- Admin: manages the product catalogue (risk level 1-5, minimum horizon) and rule parameters.
- New customer: questionnaire -> spending analysis -> plan proposal -> acceptance -> recurring orders created.
- Customer rejects or lowers the amount: nothing executes until a revised plan is accepted.
- Customer with too little data or no surplus gets an explanation instead of an investment.

Plan rules: monthly amount = 70% of the median monthly surplus of the last 6 months. Priority: emergency fund (3x median monthly expenses) -> planned expenses -> long-term investment. Money needed within 12 months goes only to low-risk liquid products. A transfer that would push the balance below 100,000 HUF is skipped.

## Acceptance criteria

- **AC1** - Monthly surpluses of 100k, 120k, 80k, 110k, 90k and 300k HUF give a suggested monthly amount of 73,500 HUF (70% of the 105k median).
- **AC2** - For a customer without an emergency fund, the first plan item fills the emergency fund before any investment.
- **AC3** - Savings for an expense due in 10 months go only to a liquid low-risk product; for risk score 2, no product above risk 2 appears in the plan.
- **AC4** - The time machine replays a plan on 12 months of stored transactions and shows the resulting savings, months where a transfer would have broken the 100,000 HUF minimum are flagged as skipped.
- **AC5** - If the median surplus is < 0, no investment plan is created, and the customer is told no surplus is available.
- **AC6** - With fewer than 3 months of transactions, no estimate is made and the app asks the customer for the expected monthly savings, with 3-5 months the plan is marked low confidence and every transfer need explicit approval.
- **AC7** - Accepting a plan creates its recurring orders exactly once, repeating the acceptance creates no duplicates, a rejected plan creates none.
- **AC8** - A negative amount or a past expense date is rejected with an error, a customer cannot view or accept another customer's plan.

## Interpretations

- The app uses no AI at runtime: the questionnaire has fixed questions with validated answers, so results are deterministic and reproducible. AI tools are used only during development (requirements, implementation, testing).
- Surplus = income - expenses per calendar month; transfers between own accounts are ignored; the median limits the effect of one-off months.
- Rule parameters (70%, 3 months, 12 months, 100,000 HUF) are configurable defaults.
- The time machine shows past behaviour only, not a forecast.
