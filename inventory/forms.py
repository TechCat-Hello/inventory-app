from django import forms
from .models import InventoryItem, Rental
from django.utils import timezone

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'category', 'quantity', 'location', 'description', 'is_available'] 

class ItemSearchForm(forms.Form):
    query = forms.CharField(required=False, label='検索', widget=forms.TextInput(attrs={'placeholder': 'キーワードを入力'}))
    stock_filter = forms.ChoiceField(
        required=False,
        label='在庫',
        choices=[
            ('', 'すべて'),         # デフォルト：フィルタなし
            ('in_stock', '在庫あり'),
            ('out_of_stock', '在庫なし')
        ]
    )

class RentalForm(forms.ModelForm):
    expected_return_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
        label='予定返却日',
        required=True  
    )

    class Meta:
        model = Rental
        fields = ['quantity', 'expected_return_date']

    def clean(self):
        cleaned_data = super().clean()
        item = self.initial.get('item')  # モデルにない item は initial から取得
        quantity = cleaned_data.get('quantity')

        if item and quantity:
            if quantity > item.quantity:
                raise forms.ValidationError(
                    f"在庫数({item.quantity})を超える貸し出しはできません。"
                )

        return cleaned_data

    def clean_expected_return_date(self):
        expected_return_date = self.cleaned_data.get('expected_return_date')
        if not expected_return_date:
            raise forms.ValidationError('返却予定日を入力してください。')
        if expected_return_date < timezone.localdate():
            raise forms.ValidationError('返却日は今日以降の日付を指定してください。')
        return expected_return_date
