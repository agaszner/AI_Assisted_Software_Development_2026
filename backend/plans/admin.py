"""Admin role: rule parameters; plans, mandates, executions and the log for inspection."""

from django.contrib import admin

from plans.models import Execution, LogEntry, Mandate, Plan, RuleConfig


@admin.register(RuleConfig)
class RuleConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: object) -> bool:
        return not RuleConfig.objects.exists()

    def has_delete_permission(self, request: object, obj: RuleConfig | None = None) -> bool:
        return False


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ["created_at", "customer", "event", "mandate_version", "clause"]


admin.site.register(Plan)
admin.site.register(Mandate)
admin.site.register(Execution)
