from django.contrib import admin
from .models import Product, Order, CartItem, Cart, OrderItem

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)