from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import InventoryItem
from django.http import HttpResponseForbidden

@login_required
def admin_dashboard_view(request):
    return render(request, 'inventory/admin_dashboard.html')

@login_required
def user_dashboard_view(request):
    return render(request, 'inventory/user_dashboard.html')

@login_required
def redirect_after_login(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')  # URL名で指定
    else:
        return redirect('user_dashboard')
    
# 一般ユーザー判定関数（例：is_staffではないユーザーを一般ユーザーとみなす）
def is_general_user(user):
    return not user.is_staff

# 一覧表示ビュー
@login_required
def item_list(request):
    if request.user.is_staff:
        return HttpResponseForbidden("管理者ユーザーはこのページにアクセスできません。")

    # 一般ユーザー向け処理続行
    items = InventoryItem.objects.filter(is_available=True)  # 利用可能な備品だけ取得
    context = {'items': items}
    return render(request, 'inventory/item_list.html', context)

# 詳細表示ビュー
@login_required
def item_detail(request, pk):
    if request.user.is_staff:
        return HttpResponseForbidden("管理者ユーザーはこのページにアクセスできません。")
    
    item = get_object_or_404(InventoryItem, pk=pk)
    return render(request, 'inventory/item_detail.html', {'item': item})



