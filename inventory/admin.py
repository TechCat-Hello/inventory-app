from django.contrib import admin
#from .models import Item    #削除予定
from .models import InventoryItem

#admin.site.register(Item)    #削除予定

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'is_available', 'updated_at')
    search_fields = ('name', 'category')
    list_filter = ('category', 'is_available')

admin.site.site_header = "在庫管理 管理画面"
admin.site.site_title = "在庫管理 Admin"
admin.site.index_title = "管理メニュー"
