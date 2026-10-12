/** TanStack Query hooks: one per endpoint. Screens never call apiFetch directly. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiFetch } from "./client";
import type {
  AccountOut,
  ActivityOut,
  AnalysisOut,
  ExecutionOut,
  IdOut,
  LoginIn,
  MandateOut,
  Me,
  PlanOut,
  ProposalOut,
  QuestionnaireIn,
  RulesOut,
  TimeMachineOut,
} from "./types";

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

/** Store the answers, then ask the rule engine for a plan (AC5, AC6 outcomes included). */
export function useSubmitAnswers() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (answers: QuestionnaireIn) => {
      await apiFetch<IdOut>("/api/questionnaire", { method: "POST", body: answers });
      return apiFetch<ProposalOut>("/api/plans", { method: "POST" });
    },
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.analysis });
    },
  });
}

export function usePlan(planId: number) {
  return useQuery({
    queryKey: keys.plan(planId),
    queryFn: () => apiFetch<PlanOut>(`/api/plans/${planId}`),
  });
}

export function useTimeMachine(planId: number) {
  return useQuery({
    queryKey: keys.timeMachine(planId),
    queryFn: () => apiFetch<TimeMachineOut>(`/api/plans/${planId}/time-machine`),
  });
}

/** Lower the amount of a proposed plan (nothing runs until it is accepted). */
export function useEditPlan(planId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (monthlyAmount: number) =>
      apiFetch<PlanOut>(`/api/plans/${planId}`, {
        method: "PATCH",
        body: { monthly_amount: monthlyAmount },
      }),
    onSuccess: async (updated) => {
      client.setQueryData(keys.plan(planId), updated);
      await client.invalidateQueries({ queryKey: keys.timeMachine(planId) });
      await client.invalidateQueries({ queryKey: keys.mandate(planId) });
    },
  });
}

/** Reject a proposed plan or pause an active one; refreshes every plan query and the log. */
export function usePlanAction(action: "reject" | "pause") {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (planId: number) =>
      apiFetch<PlanOut>(`/api/plans/${planId}/${action}`, { method: "POST" }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.activity });
    },
  });
}

export function useMandate(planId: number) {
  return useQuery({
    queryKey: keys.mandate(planId),
    queryFn: () => apiFetch<MandateOut>(`/api/plans/${planId}/mandate`),
  });
}

/** Sign the mandate with the customer's password (ADR-0004). Accepting twice creates nothing new (AC7). */
export function useAcceptPlan(planId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (password: string) =>
      apiFetch<PlanOut>(`/api/plans/${planId}/accept`, { method: "POST", body: { password } }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.activity });
      await client.invalidateQueries({ queryKey: keys.account });
    },
  });
}

export function useActivity() {
  return useQuery({
    queryKey: keys.activity,
    queryFn: () => apiFetch<ActivityOut[]>("/api/activity"),
  });
}

/** Approve one transfer of a low-confidence plan (AC6). */
export function useApproveExecution() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (executionId: number) =>
      apiFetch<ExecutionOut>(`/api/executions/${executionId}/approve`, { method: "POST" }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.activity });
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.account });
    },
  });
}

/** Propose a new amount for the active plan; nothing changes until it is signed (ADR-0004). */
export function useRevisePlan(planId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (monthlyAmount: number) =>
      apiFetch<PlanOut>(`/api/plans/${planId}/revise`, {
        method: "POST",
        body: { monthly_amount: monthlyAmount },
      }),
    onSuccess: async () => {
      await client.invalidateQueries({ queryKey: keys.plans });
      await client.invalidateQueries({ queryKey: keys.activity });
    },
  });
}
