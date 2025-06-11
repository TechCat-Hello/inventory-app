from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import InventoryItem, Rental
from django.http import HttpResponseForbidden
from .forms import InventoryItemForm, ItemSearchForm, RentalForm
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.db.models import Q


@login_required
def admin_dashboard_view(request):
    return render(request, 'inventory/admin_dashboard.html')

@login_required
def user_dashboard_view(request):
    # 自分が登録した備品
    items = InventoryItem.objects.filter(added_by=request.user)
    # 自分が借りた貸出データ
    rentals = Rental.objects.filter(user=request.user).select_related('item')

    return render(request, 'inventory/user_dashboard.html', {
        'items': items,
        'rentals': rentals, 
    })

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

    form = ItemSearchForm(request.GET or None)  # GETパラメータでフォームを初期化
    items = InventoryItem.objects.filter(is_available=True)  # 利用可能な備品だけ取得

    if form.is_valid():
        query = form.cleaned_data.get('query')
        stock_filter = form.cleaned_data.get('stock_filter')

        if query:
            items = items.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        if stock_filter == 'in_stock':
            items = items.filter(quantity__gt=0)
        elif stock_filter == 'out_of_stock':
            items = items.filter(quantity__lte=0)

    context = {
        'form': form,
        'items': items,
    }
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
    
@login_required
def rental_create(request,item_id=None):
    item = None
    if item_id:
        item = get_object_or_404(InventoryItem, pk=item_id)

    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            rental = form.save(commit=False)
            rental.item = item
            rental.user = request.user
            rental.status = 'rented'
            rental.save()
            return redirect('user_dashboard')
    else:
        form = RentalForm(initial={'item': item})
    return render(request, 'inventory/rental_create.html', {'form': form, 'item': item})

@login_required
def rental_list(request):
    rentals = Rental.objects.all().order_by('-rental_date')
    return render(request, 'inventory/rental_list.html', {'rentals': rentals})



