"""Shared test constants. Pure: no Django imports."""

from datetime import date

TODAY = date(2026, 10, 6)  # mid-month on purpose: the current month is incomplete
LAST_MONTH = date(2026, 9, 1)  # last complete calendar month before TODAY
AC1_SERIES = [100_000, 120_000, 80_000, 110_000, 90_000, 300_000]  # oldest first
