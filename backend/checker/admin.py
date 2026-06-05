from django.contrib import admin

from .models import Attempt, Symbol


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ("letter", "name")
    ordering = ("letter",)
    search_fields = ("letter", "name")


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "symbol_letter", "status", "is_correct", "confidence", "created_at")
    list_filter = ("status", "is_correct", "symbol__letter")
    search_fields = ("id", "user__username")
    readonly_fields = ("id", "created_at", "updated_at", "predicted_label", "confidence", "is_correct")
    raw_id_fields = ("user", "symbol")

    @admin.display(description="Symbol", ordering="symbol__letter")
    def symbol_letter(self, obj):
        return obj.symbol.letter
