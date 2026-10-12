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
  const targets = page.locator(
    "button, a, input:not([type=radio]):not([type=checkbox]), label:has(input[type=radio]), label:has(input[type=checkbox])",
  );
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
  await page.locator("label", { has: page.getByRole("radio", { name: "3 Medium" }) }).click(); // sr-only input
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
  await expect(
    page.getByRole("list", { name: "Plan items" }).getByRole("listitem").first(),
  ).toContainText("Emergency fund"); // AC2
  await expectTouchTargets(page);

  await page.getByRole("link", { name: "See month by month" }).click();
  await expect(page.getByRole("heading", { name: "Financial time machine" })).toBeVisible();
  await page.getByText("See month by month").click(); // open the table
  await expect(page.getByRole("table", { name: "Saved to date, month by month" })).toBeVisible(); // AC4
  await expectTouchTargets(page);

  await page.getByRole("link", { name: "Continue to mandate" }).click();
  await expect(page.getByRole("heading", { name: "Mandate · version 1" })).toBeVisible();
  await page
    .getByRole("checkbox", {
      name: "I have read the mandate and authorise these recurring orders.",
    })
    .check();
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
  await expect(page.getByRole("status").first()).toContainText("no surplus");
  await expect(page.getByText("None")).toBeVisible(); // orders created
  await expectTouchTargets(page);
});

test("layout has no horizontal scroll at 375 px", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await login(page, "dani"); // 4 months: independent of anna's state from the first test
  const overflow = () =>
    page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
  expect(await overflow()).toBeLessThanOrEqual(0);
  await expect(page.getByRole("button", { name: "Open menu" })).toBeVisible();
  await expectTouchTargets(page);
  await answerQuestionnaire(page, "0");
  await page.getByRole("link", { name: "See my plan" }).click();
  await expect(page.getByRole("complementary", { name: "Summary" })).toBeVisible(); // bottom bar
  expect(await overflow()).toBeLessThanOrEqual(0);
  await expectTouchTargets(page);
});
