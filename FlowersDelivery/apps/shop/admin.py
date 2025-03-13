from django.contrib import admin
from .models import Product, Category, Order, CartItem, Cart, OrderItem, TelegramUser, TelegramNotification



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


# admin.site.register(Product)
# admin.site.register(Order)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'status', 'total_price']
    list_filter = ['status', 'created_at']
    search_fields = ['order_key', 'user__username', 'address']
    inlines = [OrderItemInline]
    actions = ['mark_as_completed']

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')

    mark_as_completed.short_description = "Отметить как завершенные"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category']
    list_filter = ['category']
    search_fields = ['name', 'description']


admin.site.register(Category)

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