from django import forms
from .models import InventoryItem, Rental


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'category', 'quantity', 'location', 'description', 'is_available']

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'category', 'quantity', 'location']  

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
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='予定返却日',
        required=False  # 任意入力にする
    )
    class Meta:
        model = Rental
        fields = ['quantity', 'expected_return_date']

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        quantity = cleaned_data.get('quantity')

        if item and quantity:
            if quantity > item.quantity:
                raise forms.ValidationError(
                    f"在庫数({item.quantity})を超える貸し出しはできません。"
                )
        return cleaned_data
