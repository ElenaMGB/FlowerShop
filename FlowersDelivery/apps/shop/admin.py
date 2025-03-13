from django.contrib import admin
from .models import Product, Order, CartItem, Cart, OrderItem, TelegramUser, TelegramNotification

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'username', 'user', 'created_at']
    search_fields = ['telegram_id', 'username', 'user__username']
    list_filter = ['created_at']


@admin.register(TelegramNotification)
class TelegramNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'telegram_id', 'created_at', 'sent', 'sent_at']
    list_filter = ['sent', 'created_at', 'sent_at']
    search_fields = ['telegram_id', 'message_text']
    readonly_fields = ['created_at', 'sent_at']
    actions = ['mark_as_sent', 'mark_as_unsent']

    def mark_as_sent(self, request, queryset):
        from datetime import datetime
        queryset.update(sent=True, sent_at=datetime.now())

    mark_as_sent.short_description = "Отметить как отправленные"

    def mark_as_unsent(self, request, queryset):
        queryset.update(sent=False, sent_at=None)

    mark_as_unsent.short_description = "Отметить как неотправленные"