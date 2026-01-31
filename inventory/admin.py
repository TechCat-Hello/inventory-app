from django.contrib import admin
from .models import InventoryItem, Rental


# Django管理パネルへのアクセスをスーパーユーザーのみに制限
class CustomAdminSite(admin.AdminSite):
    site_header = "在庫管理 管理画面"
    site_title = "在庫管理 Admin"
    index_title = "管理メニュー"
    
    def has_permission(self, request):
        """スーパーユーザーのみがDjango管理パネルにアクセス可能"""
        return request.user.is_active and request.user.is_superuser


# カスタムAdminSiteインスタンスを作成
admin_site = CustomAdminSite(name='custom_admin')


@admin.register(InventoryItem, site=admin_site)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'is_available', 'updated_at')
    search_fields = ('name', 'category')
    list_filter = ('category', 'is_available')
    readonly_fields = ('added_by',)  # 表示のみ（編集不可）

    def save_model(self, request, obj, form, change):
        if not change:
            obj.added_by = request.user
        obj.save()

@admin.register(Rental, site=admin_site)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('item', 'user', 'quantity', 'status', 'rental_date', 'expected_return_date', 'return_date')
    search_fields = ('item__name', 'user__username')
    list_filter = ('status',)
