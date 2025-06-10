from django import forms
from .models import InventoryItem


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