from django.contrib import admin
from FlowersDelivery.apps.users.models import Product, Order

admin.site.register(Product)
admin.site.register(Order)