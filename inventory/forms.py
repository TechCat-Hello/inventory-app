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
    class Meta:
        model = Rental
        fields = ['quantity', 'return_date']
        widgets = {
            'return_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
        }
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)