from django.contrib import admin

from .models import Item, OrderItem, Order, Coupon, Refund, Address, UserProfile, Brand, SubCategory, Category


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'

admin.site.register(Brand)
admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(Address)
admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(SubCategory)
