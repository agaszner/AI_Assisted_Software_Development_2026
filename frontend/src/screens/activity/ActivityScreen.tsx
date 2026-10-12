import { useActivity } from "../../api/hooks";
import { Card } from "../../components/Card";
import { ErrorMessage } from "../../components/ErrorMessage";
import { ExecutionLog } from "../../components/ExecutionLog";

/** Activity (sidebar): the execution log on its own page. */
export function ActivityScreen() {
  const activity = useActivity();
  return (
    <div className="space-y-6">
      <h1 className="text-h1">Activity</h1>
      <Card>
        <ErrorMessage error={activity.error} />
        {activity.data ? <ExecutionLog rows={activity.data} /> : <p>Loading…</p>}
      </Card>
    </div>
  );
}
