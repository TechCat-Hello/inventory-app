from django.contrib import admin
from .models import InventoryItem, Rental


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'is_available', 'updated_at')
    search_fields = ('name', 'category')
    list_filter = ('category', 'is_available')
    readonly_fields = ('added_by',)  # 表示のみ（編集不可）

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'quantity', 'status', 'rental_date', 'expected_return_date', 'return_date')
    search_fields = ('item__name', 'user__username')
    list_filter = ('status',)

admin.site.site_header = "在庫管理 管理画面"
admin.site.site_title = "在庫管理 Admin"
admin.site.index_title = "管理メニュー"
