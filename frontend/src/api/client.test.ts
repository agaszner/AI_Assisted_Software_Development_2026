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
  mockApi({
    "GET /api/plans/9": { status: 403, body: { detail: "This plan belongs to another customer." } },
  });
  await expect(apiFetch("/api/plans/9")).rejects.toEqual(
    new ApiError(403, "This plan belongs to another customer."),
  );
});

test("a validation error list becomes one readable message", async () => {
  mockApi({
    "GET /api/x": {
      status: 422,
      body: {
        detail: [{ type: "greater_than", loc: ["body"], msg: "Input should be greater than 0" }],
      },
    },
  });
  const error = await apiFetch("/api/x").catch((caught: unknown) => caught);
  expect(error).toBeInstanceOf(ApiError);
  expect(error).toMatchObject({ status: 422, message: "Input should be greater than 0" });
});

test("a 422 keeps the field the backend names", async () => {
  document.cookie = "csrftoken=t";
  mockApi({
    "POST /api/questionnaire": {
      status: 422,
      body: {
        detail: "The due date of 'Holiday' (2026-09-01) is in the past.",
        field: "planned_expenses.1.due_on",
      },
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
