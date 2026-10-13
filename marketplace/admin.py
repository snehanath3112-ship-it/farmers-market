from django.contrib import admin
from .models import Farmer, Consumer, Hub, WeeklyCycle, Listing, Order, OrderItem, Settlement


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'village', 'is_verified')
    list_filter = ('is_verified',)
    actions = ['verify_farmers']

    @admin.action(description="Mark selected farmers as verified")
    def verify_farmers(self, request, queryset):
        queryset.update(is_verified=True)


admin.site.register(Consumer)
admin.site.register(Hub)
admin.site.register(WeeklyCycle)
admin.site.register(Listing)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Settlement)