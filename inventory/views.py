from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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



