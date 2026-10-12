import { screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { mockApi, renderScreen } from "../../test/render";
import { ActivityScreen } from "./ActivityScreen";

test("lists the activity rows from the API", async () => {
  mockApi({
    "GET /api/activity": {
      body: [
        {
          key: "event-1",
          on: "2026-10-08",
          title: "Plan proposed: 73,500 HUF a month",
          amount: 73_500,
          status: "proposed",
          mandate_version: null,
          clause: null,
          idempotency_key: null,
          logged_at: "2026-10-08T12:00:00Z",
          execution_id: null,
        },
      ],
    },
  });
  renderScreen(<ActivityScreen />, { path: "/activity" });
  expect(await screen.findByRole("heading", { name: "Activity" })).toBeInTheDocument();
  expect(await screen.findByText("Plan proposed: 73,500 HUF a month")).toBeInTheDocument();
});
