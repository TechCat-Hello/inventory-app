from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import InventoryItem, Rental, ReturnLog
from django.http import HttpResponseForbidden
from .forms import InventoryItemForm, ItemSearchForm, RentalForm
from django.core.exceptions import PermissionDenied
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
import csv
from django.http import HttpResponse
import openpyxl
from openpyxl.utils import get_column_letter
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.admin.views.decorators import staff_member_required


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
    
# 一般ユーザー判定関数
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
def rental_create(request, item_id=None):
    item = None
    if item_id:
        item = get_object_or_404(InventoryItem, pk=item_id)

    if request.method == 'POST':
        # item を initial に渡す（cleanメソッドで使用）
        form = RentalForm(request.POST, initial={'item': item})
        if form.is_valid():
            rental = form.save(commit=False)
            rental.item = item
            rental.user = request.user
            rental.status = 'borrowed'

            if rental.quantity > item.quantity:
                messages.error(request, f"在庫数（{item.quantity}個）より多くは貸し出せません。")
                return redirect('user_dashboard')

            rental.save()
            item.quantity -= rental.quantity
            item.save()

            messages.success(
                request,
                f"{rental.item.name} を貸し出しました（予定返却日: {rental.expected_return_date}）。"
            )
            return redirect('user_dashboard')
    else:
        # GETリクエスト時にも item を initial に渡す
        form = RentalForm(initial={'item': item})

    return render(request, 'inventory/rental_create.html', {'form': form, 'item': item})

@login_required
def rental_list(request):
    rentals = Rental.objects.all().order_by('-rental_date')
    return render(request, 'inventory/rental_list.html', {'rentals': rentals})

@login_required
def return_item(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)

    if request.method == 'POST' and rental.status == 'borrowed':
        if rental.quantity > 1:
            rental.quantity -= 1
            rental.save()
            # 返却履歴を作成
            ReturnLog.objects.create(rental=rental, returned_quantity=1, returned_by=request.user)
            messages.success(request, f"{rental.item.name}を1個返却しました。残り{rental.quantity}個貸出中です。")
        else:
            rental.quantity = 0
            rental.status = 'returned'
            rental.return_date = timezone.now().date()
            rental.save()
            # 最後の返却履歴も作成
            ReturnLog.objects.create(rental=rental, returned_quantity=1, returned_by=request.user)
            messages.success(request, f"{rental.item.name}をすべて返却しました。")

    return redirect('user_dashboard')

@login_required
def all_rental_history_view(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("このページは管理者のみアクセス可能です。")
    
    rentals = Rental.objects.select_related('user', 'item').order_by('-rental_date')

    # フィルター用パラメータを取得
    user_id = request.GET.get('user')
    item_id = request.GET.get('item')
    status = request.GET.get('status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if user_id:
        try:
            user_id_int = int(user_id)
            rentals = rentals.filter(user_id=user_id_int)
        except ValueError:
            pass

    if item_id:
        try:
            item_id_int = int(item_id)
            rentals = rentals.filter(item_id=item_id_int)
        except ValueError:
            pass

    if status:
        rentals = rentals.filter(status=status)
    if start_date:
        rentals = rentals.filter(rental_date__gte=start_date)
    if end_date:
        rentals = rentals.filter(rental_date__lte=end_date)

    users = User.objects.all()
    items = InventoryItem.objects.all()

    return render(request, 'inventory/all_rental_history.html', {
        'rentals': rentals,
        'users': users,
        'items': items,
        'selected_user': user_id or '',
        'selected_item': item_id or '',
        'selected_status': status or '',
        'start_date': start_date or '',
        'end_date': end_date or '',
    })

@login_required
def export_rentals_csv(request):
    rentals = Rental.objects.filter(user=request.user)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="rental_history.csv"'

    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['アイテム名', '数量', '貸出日', '返却予定日', '返却日', 'ステータス'])

    for rental in rentals:
        writer.writerow([
            rental.item.name,
            rental.quantity,
            rental.rental_date,
            rental.expected_return_date,
            rental.return_date or '未返却',
            dict(Rental.STATUS_CHOICES).get(rental.status, rental.status),
        ])

    return response

@login_required
def export_rentals_excel(request):
    rentals = Rental.objects.filter(user=request.user)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rental History"

    headers = ['アイテム名', '数量', '貸出日', '返却予定日', '返却日', 'ステータス']
    ws.append(headers)

    for rental in rentals:
        ws.append([
            rental.item.name,
            rental.quantity,
            rental.rental_date.strftime("%Y/%m/%d"),
            rental.expected_return_date.strftime("%Y/%m/%d"),
            rental.return_date.strftime("%Y/%m/%d") if rental.return_date else '未返却',
            dict(Rental.STATUS_CHOICES).get(rental.status, rental.status),
        ])

    for i in range(1, len(headers)+1):
        ws.column_dimensions[get_column_letter(i)].width = 20

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="rental_history.xlsx"'
    wb.save(response)
    return response

@login_required
def export_rentals_pdf(request):
    rentals = Rental.objects.filter(user=request.user)

    # レンダリング用のHTMLテンプレートに渡すコンテキスト
    context = {
        'rentals': rentals,
        'user': request.user,
    }

    # テンプレートをHTMLに変換
    html_string = render_to_string('inventory/rental_history_pdf.html', context)

    # PDFに変換
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    # PDFをHTTPレスポンスとして返す
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rental_history.pdf"'
    return response

@staff_member_required
def export_all_rentals_csv(request):
    rentals = Rental.objects.select_related('user', 'item').all()

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="all_rental_history.csv"'
    response.write('\ufeff')  

    writer = csv.writer(response)
    writer.writerow(['ユーザー名', 'アイテム名', '数量', '貸出日', '返却予定日', '返却日', 'ステータス'])

    for rental in rentals:
        writer.writerow([
            rental.user.username,
            rental.item.name,
            rental.quantity,
            rental.rental_date.strftime("%Y/%m/%d") if rental.rental_date else '',
            rental.expected_return_date.strftime("%Y/%m/%d") if rental.expected_return_date else '',
            rental.return_date.strftime("%Y/%m/%d") if rental.return_date else '未返却',
            dict(Rental.STATUS_CHOICES).get(rental.status, rental.status),
        ])

    return response


@staff_member_required
def export_all_rentals_excel(request):
    rentals = Rental.objects.select_related('user', 'item').all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "All Rental History"

    headers = ['ユーザー名', 'アイテム名', '数量', '貸出日', '返却予定日', '返却日', 'ステータス']
    ws.append(headers)

    for rental in rentals:
        ws.append([
            rental.user.username,
            rental.item.name,
            rental.quantity,
            rental.rental_date.strftime("%Y/%m/%d") if rental.rental_date else '',
            rental.expected_return_date.strftime("%Y/%m/%d") if rental.expected_return_date else '',
            rental.return_date.strftime("%Y/%m/%d") if rental.return_date else '未返却',
            dict(Rental.STATUS_CHOICES).get(rental.status, rental.status),
        ])

    for i in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 20

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="all_rental_history.xlsx"'
    wb.save(response)
    return response


@staff_member_required
def export_all_rentals_pdf(request):
    rentals = Rental.objects.select_related('user', 'item').all()

    context = {
        'rentals': rentals,
        'current_user': request.user,
    }

    html_string = render_to_string('inventory/all_rentals_pdf.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="all_rental_history.pdf"'
    return response