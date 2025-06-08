from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 各フィールドにBootstrapのform-controlクラスを付与
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


# （参考までに）備品管理アプリで使いそうな検索フォームや追加フォームがあればここに追加

# 備品カテゴリ選択用のフォーム
EQUIPMENT_CATEGORIES = [
    ('pc', 'パソコン'),
    ('printer', 'プリンター'),
    ('desk', '机'),
    ('chair', '椅子'),
    # 必要に応じて追加
]

class EquipmentSearchForm(forms.Form):
    category = forms.ChoiceField(
        choices=EQUIPMENT_CATEGORIES,
        required=False,
        label='カテゴリ',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    keyword = forms.CharField(
        required=False,
        label='キーワード検索',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '備品名や説明など'})
    )
