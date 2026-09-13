from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.conf import settings

# 新規登録ページ
def signup_view(request: HttpRequest) -> HttpResponse:
    if not settings.DEBUG:
        return HttpResponseForbidden("本番環境では新規登録できません。")

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            messages.error(request, 'ユーザー名またはパスワードが正しくありません。')
            return render(request, 'registration/login.html')
    return render(request, 'registration/login.html')
