# 型（Types）とバリデーションの実装説明

## 概要
このDjangoプロジェクトでは、Djangoの標準的な仕組みを使って型の定義とデータのバリデーション（検証）を行っています。

---

## 1. モデルレベルでの型定義とバリデーション

### 実装場所: `inventory/models.py`

```python
class InventoryItem(models.Model):
    name = models.CharField(max_length=100)  # 型: 文字列、最大100文字
    category = models.CharField(max_length=50)  # 型: 文字列、最大50文字
    quantity = models.PositiveIntegerField()  # 型: 正の整数のみ（0以上）
    location = models.CharField(max_length=100, blank=True)  # 空欄OK
    description = models.TextField(blank=True)  # 長文用、空欄OK
    is_available = models.BooleanField(default=True)  # 型: True/False
    created_at = models.DateTimeField(auto_now_add=True)  # 作成時に自動設定
    updated_at = models.DateTimeField(auto_now=True)  # 更新時に自動設定
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)  # 外部キー
```

### ポイント
- **PositiveIntegerField**: 負の数を自動的に弾く（0以上のみ許可）
- **CharField(max_length=100)**: 文字数制限を強制
- **blank=True/False**: 空欄の可否をデータベースレベルで制御
- **ForeignKey**: リレーション（関連）を型安全に実装
- **auto_now/auto_now_add**: タイムスタンプを自動管理

### 選択肢の制限（Choices）

```python
class Rental(models.Model):
    STATUS_CHOICES = [
        ('borrowed', '貸出中'),
        ('returned', '返却済み'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
```

- **choices**: 許可された値のみをデータベースに保存
- それ以外の値はエラーになる

---

## 2. フォームレベルでのバリデーション

### 実装場所: `inventory/forms.py`

#### 基本的なバリデーション

```python
class RentalForm(forms.ModelForm):
    expected_return_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='予定返却日',
        required=True  # 必須フィールド
    )
```

#### カスタムバリデーション（単一フィールド）

```python
def clean_expected_return_date(self):
    """個別フィールドのバリデーション"""
    expected_return_date = self.cleaned_data.get('expected_return_date')
    
    # 必須チェック
    if not expected_return_date:
        raise forms.ValidationError('返却予定日を入力してください。')
    
    # 過去の日付チェック
    if expected_return_date < timezone.localdate():
        raise forms.ValidationError('返却日は今日以降の日付を指定してください。')
    
    return expected_return_date
```

#### カスタムバリデーション（複数フィールド）

```python
def clean(self):
    """複数フィールドを組み合わせたバリデーション"""
    cleaned_data = super().clean()
    item = self.initial.get('item')  # 外部から渡された情報
    quantity = cleaned_data.get('quantity')

    # 在庫チェック
    if item and quantity:
        if quantity > item.quantity:
            raise forms.ValidationError(
                f"在庫数({item.quantity})を超える貸し出しはできません。"
            )

    return cleaned_data
```

### ポイント
- **clean_<field_name>()**: 個別フィールドのバリデーション
- **clean()**: 複数フィールドを組み合わせたバリデーション
- **forms.ValidationError**: エラーをユーザーに表示
- **cleaned_data**: バリデーション済みのデータ

---

## 3. ビューレベルでのバリデーション

### 実装場所: `inventory/views.py`

```python
@login_required
@transaction.atomic
def rental_create(request, item_id=None):
    item = get_object_or_404(InventoryItem, pk=item_id)

    if request.method == 'POST':
        form = RentalForm(request.POST, initial={'item': item})
        
        if form.is_valid():  # フォームバリデーションを実行
            rental = form.save(commit=False)
            rental.item = item
            rental.user = request.user
            rental.status = 'borrowed'

            # ビジネスロジックレベルでの追加チェック
            if rental.quantity > item.quantity:
                messages.error(request, f"在庫数（{item.quantity}個）より多くは貸し出せません。")
                return redirect('user_dashboard')

            # データベース更新
            rental.save()
            item.quantity -= rental.quantity
            item.save()
```

### ポイント
- **@login_required**: ログイン必須（認証チェック）
- **@transaction.atomic**: データベーストランザクション（整合性保証）
- **form.is_valid()**: フォームレベルのバリデーションを実行
- **追加のビジネスロジック**: フォームでは検証できない複雑なチェック

---

## 4. テストコードでのバリデーション検証

### 実装場所: `inventory/tests.py`

```python
def test_rental_prevents_overselling(self):
    """在庫不足時に貸出がブロックされることを確認"""
    self.client.login(username='testuser', password='testpass123')
    
    # 在庫以上の数量を借りようとする
    response = self.client.post(reverse('rental_create', args=[self.item.id]), {
        'quantity': 100,  # 在庫は10個なので100個は借りられない
        'expected_return_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
    }, follow=True)
    
    # 在庫が減っていないことを確認
    self.item.refresh_from_db()
    self.assertEqual(self.item.quantity, 10)
```

---

## 5. Pythonの型ヒント（Type Hints）の追加例

### 現状の課題
現在のプロジェクトでは、Pythonの型ヒント（Type Hints）を使用していません。

### 改善案

```python
from typing import Optional
from django.http import HttpRequest, HttpResponse

def rental_create(
    request: HttpRequest, 
    item_id: Optional[int] = None
) -> HttpResponse:
    """貸出作成ビュー
    
    Args:
        request: HTTPリクエストオブジェクト
        item_id: 備品ID（オプショナル）
    
    Returns:
        HttpResponse: レンダリングされたHTMLまたはリダイレクト
    """
    item: Optional[InventoryItem] = None
    if item_id:
        item = get_object_or_404(InventoryItem, pk=item_id)
    # ...
```

### 型チェックツール
- **mypy**: Pythonコードの型チェックを静的解析
- **pylint**: コード品質チェック
- **black**: コードフォーマッター

---

## 6. Pydanticの使用例（参考）

### Pydanticとは
FastAPIなどで使われるデータバリデーションライブラリ。Djangoでは標準的には使いませんが、API開発では人気です。

### 例（DjangoではなくFastAPIの場合）

```python
from pydantic import BaseModel, validator, Field
from datetime import date

class RentalCreate(BaseModel):
    item_id: int = Field(..., gt=0)  # 1以上の整数
    quantity: int = Field(..., gt=0, le=100)  # 1〜100の範囲
    expected_return_date: date
    
    @validator('expected_return_date')
    def validate_return_date(cls, v):
        if v < date.today():
            raise ValueError('返却日は今日以降の日付を指定してください')
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v, values):
        # itemの在庫数と比較するような複雑なチェックも可能
        return v
```

---

## 面接で説明する際のポイント

### 1. 多層防御（Defense in Depth）
- **フロントエンド**: HTML5のバリデーション（`type="date"`, `required`）
- **フォームレベル**: Djangoフォームでのバリデーション
- **ビジネスロジックレベル**: ビューでの追加チェック
- **データベースレベル**: モデルフィールドの制約

### 2. なぜ複数レイヤーでバリデーションするのか
- **セキュリティ**: フロントエンドは簡単に回避できる
- **データ整合性**: データベースレベルで確実に保証
- **ユーザー体験**: 早い段階でエラーを表示
- **保守性**: バリデーションロジックを一箇所に集約

### 3. このプロジェクトでの実装例
```
1. モデル: PositiveIntegerField で負の数を防ぐ
2. フォーム: clean()メソッドで在庫数を超える貸出を防ぐ
3. ビュー: 追加のビジネスロジックでダブルチェック
4. テスト: バリデーションが正しく動作することを検証
```

### 4. 改善提案（次のステップ）
- Pythonの型ヒントを追加してコードの可読性を向上
- mypyで静的型チェックを導入
- より詳細なエラーメッセージの国際化（i18n）
- API化する場合はDjango REST FrameworkのSerializerを使用

---

## まとめ

このプロジェクトでは：
1. **Djangoのモデルフィールド**で型とデータベース制約を定義
2. **Djangoフォーム**でユーザー入力のバリデーション
3. **ビューロジック**でビジネスルールを検証
4. **テストコード**でバリデーションの正確性を保証

Pydanticは使用していませんが、DjangoのFormとModelが同様の役割を果たしています。
