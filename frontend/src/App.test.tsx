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
