/** TanStack Query hooks: one per endpoint. Screens never call apiFetch directly. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiFetch } from "./client";
import type { AccountOut, AnalysisOut, LoginIn, Me, PlanOut, RulesOut } from "./types";

export const keys = {
  me: ["me"],
  account: ["account"],
  rules: ["rules"],
  analysis: ["analysis"],
  plans: ["plans"],
  plan: (id: number) => ["plans", id],
  timeMachine: (id: number) => ["plans", id, "time-machine"],
  mandate: (id: number) => ["plans", id, "mandate"],
  activePlan: ["plans", "active"],
  activity: ["activity"],
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

export function useAccount() {
  return useQuery({ queryKey: keys.account, queryFn: () => apiFetch<AccountOut>("/api/account") });
}

export function useRules() {
  return useQuery({ queryKey: keys.rules, queryFn: () => apiFetch<RulesOut>("/api/rules") });
}

export function useAnalysis() {
  return useQuery({
    queryKey: keys.analysis,
    queryFn: () => apiFetch<AnalysisOut>("/api/analysis"),
  });
}

/** The accepted or paused plan, or null when there is none (404). */
export function useActivePlan() {
  return useQuery({
    queryKey: keys.activePlan,
    queryFn: () => orNull(apiFetch<PlanOut>("/api/plans/active"), 404),
  });
}
