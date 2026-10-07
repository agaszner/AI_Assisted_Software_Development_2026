# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Django 5 + Django Ninja backend skeleton with session login, `customer` / `admin` roles and a Makefile (ADR-0001).
- `make docs-check`: AC ↔ traceability, referenced tests exist, changelog touched (AGENTS.md 8.6).
- ADR-0002 records rule interpretations for spec-silent edge cases and the M2 scope.
- Injected `Clock` (`core/clock.py`), integer-forint money helpers, calendar-month helpers and default rule parameters (`rules/defaults.py`).
- Purity test: `rules/` may not import Django or read the system clock (golden rule 4).
