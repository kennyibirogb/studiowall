from django.contrib import admin
from django.utils.html import format_html

from .models import Order, Painting, SiteProfile, CommissionRequest, CommissionReference

admin.site.site_header = "Studio Wall admin"
admin.site.site_title = "Studio Wall"


@admin.register(Painting)
class PaintingAdmin(admin.ModelAdmin):
    list_display = ("thumb", "title", "status", "price", "price_amount", "year", "position")
    list_display_links = ("thumb", "title")
    list_editable = ("status", "price", "price_amount", "position")
    list_filter = ("status",)
    search_fields = ("title", "medium")
    prepopulated_fields = {"slug": ("title",)}

    @admin.display(description="Painting")
    def thumb(self, obj):
        return format_html('<img src="{}" style="height:52px;border-radius:2px">', obj.image.url)


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("created", "painting", "customer", "buyer_email", "phone", "amount", "status")
    list_filter = ("status",)
    search_fields = ("painting__title", "customer__username", "customer__email", "phone")
    readonly_fields = ("customer", "painting", "amount", "phone", "address", "reference", "created", "paid_at")
    actions = ["mark_paid"]

    def has_add_permission(self, request):
        return False

    @admin.display(description="Email")
    def buyer_email(self, obj):
        return obj.customer.email

    @admin.action(description="Mark selected orders as paid (painting becomes Sold)")
    def mark_paid(self, request, queryset):
        for order in queryset.exclude(status=Order.PAID):
            order.mark_paid()



class CommissionReferenceInline(admin.TabularInline):
    model = CommissionReference
    extra = 0

@admin.register(CommissionRequest)
class CommissionRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "status", "created")
    list_filter = ("status", "created")
    search_fields = ("name", "email", "description")
    inlines = [CommissionReferenceInline]