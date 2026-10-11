import { QueryClientProvider, type QueryClient } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { vi } from "vitest";
import { makeQueryClient } from "../api/queryClient";
import { App, createQueryClient } from "../App";

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
