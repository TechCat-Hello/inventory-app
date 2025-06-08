from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from .forms import CustomUserCreationForm
from .models import Profile
from django.contrib.auth import authenticate, login


# ログインページ
def login_view(request):
    return render(request, 'registration/login.html')


# 新規登録ページ
def signup_view(request):
    #新規登録を無効化する場合は以下のコードを削除
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

    #新規登録を無効化する場合は以下のコードを使用
    ##message = "このアプリでは新規登録はできません"
    #return render(request, 'signup.html', {'message': message})

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
            return render(request, 'login.html', {'error': 'ユーザー名またはパスワードが正しくありません。'})
    return render(request, 'login.html')

    
