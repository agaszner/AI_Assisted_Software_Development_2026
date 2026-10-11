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
  if (
    typeof body === "object" &&
    body !== null &&
    "field" in body &&
    typeof body.field === "string"
  ) {
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
