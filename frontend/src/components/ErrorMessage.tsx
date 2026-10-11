/** Shows an Error's message (API errors carry the backend's detail text) or a string. */
export function ErrorMessage({ error }: { error: unknown }) {
  if (error === null || error === undefined || error === "") return null;
  const text =
    typeof error === "string"
      ? error
      : error instanceof Error
        ? error.message
        : "Something went wrong.";
  return (
    <p
      role="alert"
      className="rounded-md border border-danger bg-danger-bg p-3 text-body text-danger"
    >
      {text}
    </p>
  );
}
