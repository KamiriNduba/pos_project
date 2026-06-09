# inventory/admin.py
from django.contrib import admin
from .models import Batch, StockMovement, PurchaseOrder, StockCount, StoreTransfer, InventoryAlert


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['batch_number', 'product', 'remaining_quantity', 'expiry_date', 'status']
    list_filter = ['status', 'product', 'location']
    search_fields = ['batch_number', 'product__name', 'product__sku']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('batch_number', 'product', 'status')
        }),
        ('Quantities', {
            'fields': ('quantity', 'remaining_quantity')
        }),
        ('Dates', {
            'fields': ('manufacturing_date', 'expiry_date')
        }),
        ('Purchase Info', {
            'fields': ('purchase_order', 'purchase_price', 'supplier')
        }),
        ('Location', {
            'fields': ('location', 'shelf_location')
        }),
        ('Quality Control', {
            'fields': ('quality_passed', 'quality_notes', 'inspected_by', 'inspected_at')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Rest of your inventory admin registrations...