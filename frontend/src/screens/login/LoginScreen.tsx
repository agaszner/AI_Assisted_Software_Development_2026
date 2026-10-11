import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { useLogin } from "../../api/hooks";
import { Button } from "../../components/Button";
import { ErrorMessage } from "../../components/ErrorMessage";
import { Icon } from "../../components/Icon";
import { TextField } from "../../components/TextField";

const POINTS = [
  "Fixed, transparent rules",
  "Financial time machine on your own history",
  "Orders run only under a mandate you sign",
];

/** Figma 01 Login (5:73): brand panel (hidden below 1024 px) and form. */
export function LoginScreen() {
  const login = useLogin();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    login.mutate({ username, password }, { onSuccess: () => navigate("/") });
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="hidden flex-col justify-center gap-6 bg-primary p-16 text-on-primary lg:flex">
        <p className="text-h2">SaverAI</p>
        <h2 className="text-number">Save what you already don&apos;t spend.</h2>
        <p className="max-w-narrow text-h3 font-normal">
          SaverAI looks at your past months, suggests a monthly amount and replays it on your own
          history before anything runs.
        </p>
        <ul className="space-y-3">
          {POINTS.map((point) => (
            <li key={point} className="flex items-center gap-3">
              <Icon name="check" />
              {point}
            </li>
          ))}
        </ul>
      </section>
      <main className="flex items-center justify-center bg-surface px-4">
        <form className="w-full max-w-100 space-y-5" onSubmit={submit}>
          <h1 className="text-h1">Log in</h1>
          <p className="text-text-muted">Use a demo persona, e.g. anna.</p>
          <TextField
            label="Username"
            autoComplete="username"
            required
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
          <TextField
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <ErrorMessage error={login.error} />
          <Button type="submit" className="w-full" disabled={login.isPending}>
            Log in
            <Icon name="chevron-right" />
          </Button>
          <p className="text-caption text-text-muted">
            Demo only. Transactions, products and orders are simulated; no real bank is connected.
          </p>
        </form>
      </main>
    </div>
  );
}
