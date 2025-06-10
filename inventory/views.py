from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import InventoryItem
from django.http import HttpResponseForbidden
from .forms import InventoryItemForm
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy


@login_required
def admin_dashboard_view(request):
    return render(request, 'inventory/admin_dashboard.html')

@login_required
def user_dashboard_view(request):
    items = InventoryItem.objects.filter(added_by=request.user)  # ← ログインユーザーの備品のみ取得
    return render(request, 'inventory/user_dashboard.html', {'items': items})

@login_required
def redirect_after_login(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')  # URL名で指定
    else:
        return redirect('user_dashboard')
    
# 一般ユーザー判定関数（例：is_staffではないユーザーを一般ユーザーとみなす）
def is_general_user(user):
    return user.is_authenticated and not user.is_staff

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

# 登録
@login_required
@user_passes_test(is_general_user)
def item_create(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.added_by = request.user
            item.save()
            return redirect('item_detail', pk=item.pk)  # 備品一覧にリダイレクト
    else:
        form = InventoryItemForm()
    return render(request, 'inventory/item_form.html', {'form': form, 'title': '備品登録'})

# 編集
@login_required
def item_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk, added_by=request.user)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('user_dashboard')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'inventory/item_form.html', {'form': form, 'title': '備品編集'})

# 削除（確認画面あり）
@login_required
def item_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk, added_by=request.user)
    if request.method == 'POST':
        item.delete()
        return redirect('user_dashboard')
    return render(request, 'inventory/item_confirm_delete.html', {'item': item})

@login_required
def edit_item(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)

    # 一般ユーザーは自分が登録したものだけ編集可能
    if not request.user.is_superuser and item.user != request.user:
        return redirect('user_dashboard')  # 不正アクセス防止

    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('user_dashboard')  # または 'item_detail', args=[item.pk]
    else:
        form = InventoryItemForm(instance=item)

    return render(request, 'inventory/edit_item.html', {'form': form, 'item': item})

class InventoryItemDeleteView(DeleteView):
    model = InventoryItem
    template_name = 'inventory/item_confirm_delete.html'
    success_url = reverse_lazy('items_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


