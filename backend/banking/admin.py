"""Admin role: product catalogue; accounts and transactions for inspection."""

from django.contrib import admin

from banking.models import Account, Product, Transaction


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "risk_level", "min_horizon_months", "liquid", "active"]
    list_filter = ["risk_level", "liquid", "active"]


admin.site.register(Account)
admin.site.register(Transaction)
