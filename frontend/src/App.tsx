import type { QueryClient } from "@tanstack/react-query";
import { Navigate, Outlet, Route, Routes, useNavigate } from "react-router";
import { keys, useLogout, useMe } from "./api/hooks";
import { makeQueryClient } from "./api/queryClient";
import { AppShell } from "./components/AppShell";
import { ErrorMessage } from "./components/ErrorMessage";
import { HomeScreen } from "./screens/home/HomeScreen";
import { LoginScreen } from "./screens/login/LoginScreen";

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
          {/* Task 17 replaces "/plan" and "/activity". */}
          <Route path="/" element={<HomeScreen />} />
          <Route path="/plan" element={<h1 className="text-h1">Your savings plan</h1>} />
          <Route path="/activity" element={<h1 className="text-h1">Activity</h1>} />
        </Route>
        {/* Flow routes (Tasks 11–16) go here: they render FlowLayout themselves. */}
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
