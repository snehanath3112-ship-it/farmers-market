from django.contrib import admin
from .models import Farmer, Consumer, Hub, WeeklyCycle, Listing, Order, OrderItem, Settlement

admin.site.register(Farmer)
admin.site.register(Consumer)
admin.site.register(Hub)
admin.site.register(WeeklyCycle)
admin.site.register(Listing)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Settlement)