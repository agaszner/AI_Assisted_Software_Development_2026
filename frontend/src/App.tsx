import type { QueryClient } from "@tanstack/react-query";
import { Navigate, Outlet, Route, Routes, useNavigate } from "react-router";
import { keys, useLogout, useMe } from "./api/hooks";
import { makeQueryClient } from "./api/queryClient";
import { AppShell } from "./components/AppShell";
import { ErrorMessage } from "./components/ErrorMessage";
import { ActivePlanScreen } from "./screens/active-plan/ActivePlanScreen";
import { ActivityScreen } from "./screens/activity/ActivityScreen";
import { AnalysisScreen } from "./screens/analysis/AnalysisScreen";
import { HomeScreen } from "./screens/home/HomeScreen";
import { LoginScreen } from "./screens/login/LoginScreen";
import { MandateScreen } from "./screens/mandate/MandateScreen";
import { PlanReviewScreen } from "./screens/plan-review/PlanReviewScreen";
import { QuestionnaireScreen } from "./screens/questionnaire/QuestionnaireScreen";
import { TimeMachineScreen } from "./screens/time-machine/TimeMachineScreen";

/** Any 401 (expired session) clears the user, so RequireLogin redirects to /login. */
export function createQueryClient(): QueryClient {
  const client: QueryClient = makeQueryClient(() => client.setQueryData(keys.me, null));
  return client;
}

function RequireLogin() {
  const me = useMe();
  if (me.isPending) return <p className="p-4">Loading…</p>;
  if (me.isError) return <ErrorMessage error={me.error} />;
  return me.data === null ? <Navigate to="/login" replace /> : <Outlet />;
}

/** Home, Savings plan and Activity share the sidebar layout (Figma 02, 08). */
export function CustomerLayout() {
  const me = useMe();
  const logout = useLogout();
  const navigate = useNavigate();
  if (!me.data) return null;
  return (
    <AppShell
      user={me.data}
      onLogout={() => logout.mutate(undefined, { onSettled: () => navigate("/login") })}
    >
      <Outlet />
    </AppShell>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginScreen />} />
      <Route element={<RequireLogin />}>
        <Route element={<CustomerLayout />}>
          <Route path="/" element={<HomeScreen />} />
          <Route path="/plan" element={<ActivePlanScreen />} />
          <Route path="/activity" element={<ActivityScreen />} />
        </Route>
        {/* Flow routes (Tasks 11–16) go here: they render FlowLayout themselves. */}
        <Route path="/questionnaire" element={<QuestionnaireScreen />} />
        <Route path="/plans/:planId/analysis" element={<AnalysisScreen />} />
        <Route path="/plans/:planId" element={<PlanReviewScreen />} />
        <Route path="/plans/:planId/time-machine" element={<TimeMachineScreen />} />
        <Route path="/plans/:planId/mandate" element={<MandateScreen />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
