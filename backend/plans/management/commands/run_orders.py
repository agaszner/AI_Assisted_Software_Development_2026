"""Execute this month's recurring orders. Idempotent: safe to run repeatedly (cron, demo).
Replaces APScheduler in M2 (ADR-0002)."""

from collections import Counter
from datetime import date, datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from core.clock import get_clock
from plans.execution import run_monthly_orders
from plans.services import PlanConflict


class Command(BaseCommand):
    help = "Execute this month's recurring orders through the mandate check."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--period", type=year_month, help="Month to execute, YYYY-MM (default: current month)."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            executions = run_monthly_orders(get_clock(), options["period"])
        except PlanConflict as error:
            raise CommandError(str(error)) from error
        counts = Counter(str(e.status) for e in executions)
        summary = ", ".join(f"{status}={n}" for status, n in sorted(counts.items()))
        self.stdout.write(f"{len(executions)} orders processed: {summary}")


def year_month(value: str) -> date:
    return datetime.strptime(value, "%Y-%m").date()  # noqa: DTZ007  parses a month, no time zone
