# データフロー解説：ボタンを押してからデータベースに保存されるまで

## 概要
このドキュメントでは、フロントエンド（ブラウザ）でボタンを押してから、サーバー側で処理され、PostgreSQLデータベースに保存されるまでの「データの旅」を具体的に説明します。

**具体例**: 「備品を貸し出す」ボタンを押した場合

---

## データフローの全体像

```
[1] フロントエンド（ブラウザ）
    ↓ HTTPリクエスト（POST）
[2] Django URLルーティング
    ↓
[3] ビュー関数
    ↓
[4] フォームバリデーション
    ↓
[5] ビジネスロジック処理
    ↓
[6] ORM（Object-Relational Mapping）
    ↓
[7] PostgreSQLデータベース
    ↓ レスポンス
[8] ユーザーにフィードバック
```

---

## 詳細なステップ解説

### ステップ1: フロントエンド（ブラウザ）

**ファイル**: `inventory/templates/inventory/rental_create.html`

```html
<form method="post">
  {% csrf_token %}
  
  <div>
    <label for="id_quantity">数量</label>
    {{ form.quantity }}
  </div>

  <div>
    <label for="id_expected_return_date">予定返却日</label>
    {{ form.expected_return_date }}
  </div>

  <button type="submit">貸し出し登録</button>
</form>
```

**何が起きるか**:
1. ユーザーが数量（例: 3）と予定返却日（例: 2026-02-07）を入力
2. 「貸し出し登録」ボタンをクリック
3. ブラウザがHTTP POSTリクエストを送信

**送信されるデータ**:
```
POST /rental/create/5/
Content-Type: application/x-www-form-urlencoded

csrfmiddlewaretoken=abc123...
quantity=3
expected_return_date=2026-02-07
```

**セキュリティ**: `{% csrf_token %}` でクロスサイトリクエストフォージェリ（CSRF）攻撃を防ぐ

---

### ステップ2: Django URLルーティング

**ファイル**: `config/urls.py` → `inventory/urls.py`

```python
# config/urls.py
urlpatterns = [
    path('', include('inventory.urls')),
]

# inventory/urls.py
urlpatterns = [
    path('rental/create/<int:item_id>/', views.rental_create, name='rental_create'),
]
```

**何が起きるか**:
1. DjangoがURL `/rental/create/5/` を受け取る
2. URLパターンとマッチング
3. `item_id=5` を抽出
4. `views.rental_create` 関数を呼び出す

**ルーティングの仕組み**:
- `<int:item_id>`: URLから整数を取り出して引数として渡す
- `name='rental_create'`: テンプレートで `{% url 'rental_create' item.id %}` として使える

---

### ステップ3: ビュー関数の処理

**ファイル**: `inventory/views.py`

```python
@login_required
@transaction.atomic
def rental_create(request, item_id=None):
    # [3-1] 備品をデータベースから取得
    item = get_object_or_404(InventoryItem, pk=item_id)

    # [3-2] POSTリクエストかチェック
    if request.method == 'POST':
        # [3-3] フォームにデータを渡す
        form = RentalForm(request.POST, initial={'item': item})
        
        # [3-4] バリデーションを実行
        if form.is_valid():
            # [3-5] データベースに保存（後述）
            ...
    else:
        # GETリクエストの場合は空のフォームを表示
        form = RentalForm(initial={'item': item})

    return render(request, 'inventory/rental_create.html', {'form': form, 'item': item})
```

**デコレータの役割**:
- `@login_required`: ログインしていないユーザーを弾く
- `@transaction.atomic`: データベース操作をトランザクションで管理（失敗したら全部ロールバック）

---

### ステップ4: フォームバリデーション

**ファイル**: `inventory/forms.py`

```python
class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['quantity', 'expected_return_date']

    def clean(self):
        """複数フィールドのバリデーション"""
        cleaned_data = super().clean()
        item = self.initial.get('item')
        quantity = cleaned_data.get('quantity')

        # [4-1] 在庫数チェック
        if item and quantity:
            if quantity > item.quantity:
                raise forms.ValidationError(
                    f"在庫数({item.quantity})を超える貸し出しはできません。"
                )

        return cleaned_data

    def clean_expected_return_date(self):
        """返却日のバリデーション"""
        expected_return_date = self.cleaned_data.get('expected_return_date')
        
        # [4-2] 過去の日付チェック
        if expected_return_date < timezone.localdate():
            raise forms.ValidationError('返却日は今日以降の日付を指定してください。')
        
        return expected_return_date
```

**バリデーションの流れ**:
1. 型チェック: `quantity` が整数か、`expected_return_date` が日付か
2. 個別フィールドチェック: `clean_expected_return_date()` で過去の日付を弾く
3. 複数フィールドチェック: `clean()` で在庫数を超えていないか確認

**もしエラーがあれば**:
- フォームは `is_valid()` で `False` を返す
- エラーメッセージをテンプレートに表示
- データベースには保存されない

---

### ステップ5: ビジネスロジック処理

**ファイル**: `inventory/views.py`

```python
if form.is_valid():
    # [5-1] フォームデータからRentalオブジェクトを作成（まだ保存しない）
    rental = form.save(commit=False)
    
    # [5-2] 追加情報を設定
    rental.item = item
    rental.user = request.user
    rental.status = 'borrowed'

    # [5-3] ダブルチェック（念のため）
    if rental.quantity > item.quantity:
        messages.error(request, f"在庫数（{item.quantity}個）より多くは貸し出せません。")
        return redirect('user_dashboard')

    # [5-4] データベースに保存
    rental.save()
    
    # [5-5] 在庫を減らす
    item.quantity -= rental.quantity
    item.save()

    # [5-6] 成功メッセージを表示
    messages.success(request, f"{rental.item.name} を貸し出しました。")
    
    # [5-7] ダッシュボードにリダイレクト
    return redirect('user_dashboard')
```

**重要なポイント**:
- `commit=False`: いったんオブジェクトを作るが、まだDBに保存しない
- `rental.save()`: ここで初めてデータベースに保存
- `@transaction.atomic`: もし途中でエラーが起きたら、全ての変更をロールバック

---

### ステップ6: ORM（Object-Relational Mapping）

**Djangoのモデル**: `inventory/models.py`

```python
class Rental(models.Model):
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expected_return_date = models.DateField()
    rental_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
```

**ORMが生成するSQL**:

```sql
BEGIN;  -- トランザクション開始

-- [6-1] Rentalテーブルに新しいレコードを挿入
INSERT INTO inventory_rental (
    item_id, 
    quantity, 
    user_id, 
    expected_return_date, 
    rental_date, 
    return_date, 
    status
) VALUES (
    5,                    -- item_id
    3,                    -- quantity
    1,                    -- user_id
    '2026-02-07',         -- expected_return_date
    '2026-01-31 13:30:00',-- rental_date
    NULL,                 -- return_date（まだ返却していない）
    'borrowed'            -- status
);

-- [6-2] InventoryItemテーブルの在庫を更新
UPDATE inventory_inventoryitem 
SET quantity = quantity - 3,
    updated_at = '2026-01-31 13:30:00'
WHERE id = 5;

COMMIT;  -- トランザクション完了
```

**ORMの利点**:
- SQLを書かなくてもデータベース操作ができる
- データベースの種類（PostgreSQL、MySQL、SQLite）を気にしなくてよい
- Pythonのオブジェクトとして扱える

---

### ステップ7: PostgreSQLデータベース

**実際のデータベース操作**:

```
PostgreSQLサーバー
├─ データベース: postgres
│  ├─ テーブル: inventory_rental
│  │  └─ 新しいレコード追加:
│  │      id: 42
│  │      item_id: 5
│  │      quantity: 3
│  │      user_id: 1
│  │      expected_return_date: 2026-02-07
│  │      rental_date: 2026-01-31 13:30:00
│  │      status: 'borrowed'
│  │
│  ├─ テーブル: inventory_inventoryitem
│  │  └─ レコード更新:
│  │      id: 5
│  │      quantity: 10 → 7 に変更
│  │      updated_at: 2026-01-31 13:30:00
```

**トランザクションの仕組み**:
1. `BEGIN`: 処理開始
2. 複数のSQL実行（INSERT、UPDATE）
3. エラーなし → `COMMIT`: 確定
4. エラーあり → `ROLLBACK`: 全て取り消し

**データ整合性の保証**:
- もし在庫更新に失敗したら、貸出レコードも作成されない
- 「貸出だけ記録されて在庫が減らない」という不整合が起きない

---

### ステップ8: ユーザーにフィードバック

**レスポンスの流れ**:

```python
# ビュー関数の最後
messages.success(request, f"{rental.item.name} を貸し出しました。")
return redirect('user_dashboard')
```

**何が起きるか**:
1. 成功メッセージをセッションに保存
2. HTTP 302リダイレクトレスポンスを返す
3. ブラウザが `/dashboard/` に移動
4. ダッシュボードページでメッセージを表示

**テンプレートでの表示**: `templates/base.html`

```html
{% if messages %}
  {% for message in messages %}
    <div class="alert alert-{{ message.tags }}">
      {{ message }}
    </div>
  {% endfor %}
{% endif %}
```

**ユーザーが見るもの**:
```
✅ ノートPC を貸し出しました（予定返却日: 2026-02-07）。
```

---

## データの流れの可視化

### タイムライン

```
時刻       | 場所                | 何が起きているか
-----------|---------------------|----------------------------------
13:30:00   | ブラウザ            | ユーザーがボタンをクリック
13:30:00   | ネットワーク        | HTTP POSTリクエスト送信
13:30:01   | Djangoサーバー      | URLルーティング
13:30:01   | Djangoビュー        | rental_create関数実行開始
13:30:01   | フォーム            | バリデーション実行
13:30:01   | ビジネスロジック    | 在庫チェック
13:30:02   | Django ORM          | SQLクエリ生成
13:30:02   | PostgreSQL          | BEGIN トランザクション開始
13:30:02   | PostgreSQL          | INSERT INTO rental...
13:30:02   | PostgreSQL          | UPDATE inventoryitem...
13:30:02   | PostgreSQL          | COMMIT 確定
13:30:03   | Djangoビュー        | リダイレクトレスポンス生成
13:30:03   | ネットワーク        | HTTP 302レスポンス送信
13:30:03   | ブラウザ            | ダッシュボードページに移動
13:30:04   | ブラウザ            | 成功メッセージ表示
```

---

## エラーハンドリング

### 例: 在庫不足の場合

```
[フォームバリデーション]
quantity = 100, item.quantity = 10
→ ValidationError発生
→ form.is_valid() が False を返す
→ データベースに保存されない
→ エラーメッセージをテンプレートに表示
```

### 例: データベースエラーの場合

```
[トランザクション中にエラー]
rental.save() は成功
item.save() でエラー発生
→ @transaction.atomic が検知
→ ROLLBACK実行
→ rental.save() も取り消される
→ 500エラーまたはエラーページ表示
```

---

## セキュリティ対策

### 1. CSRF対策
```html
{% csrf_token %}
```
- フォームにトークンを埋め込む
- サーバーで検証（正しいサイトからのリクエストか確認）

### 2. 認証チェック
```python
@login_required
```
- ログインしていないユーザーを弾く
- ログインページにリダイレクト

### 3. SQLインジェクション対策
```python
# ❌ 危険（生のSQL）
query = f"INSERT INTO rental VALUES ({item_id}, {quantity})"

# ✅ 安全（ORMを使用）
rental = Rental.objects.create(item_id=item_id, quantity=quantity)
```
- ORMがパラメータをエスケープ
- SQLインジェクション攻撃を防ぐ

### 4. XSS（クロスサイトスクリプティング）対策
```html
<!-- Djangoが自動的にエスケープ -->
<p>{{ item.name }}</p>
<!-- <script>alert('hack')</script> → エスケープされて表示されるだけ -->
```

---

## パフォーマンス最適化

### 1. N+1問題の回避

```python
# ❌ 遅い（N+1クエリ問題）
rentals = Rental.objects.all()
for rental in rentals:
    print(rental.item.name)  # 毎回SQLクエリ発行

# ✅ 速い（JOINで一度に取得）
rentals = Rental.objects.select_related('item', 'user').all()
for rental in rentals:
    print(rental.item.name)  # すでに取得済み
```

### 2. インデックスの活用

```python
class Rental(models.Model):
    status = models.CharField(max_length=20, db_index=True)  # インデックス
    rental_date = models.DateTimeField(db_index=True)  # インデックス
```
- よく検索するフィールドにインデックスを作成
- クエリが高速化

---

## まとめ

### データフローの要点

1. **フロントエンド**: ユーザーがフォーム送信 → HTTP POSTリクエスト
2. **ルーティング**: DjangoがURLをビュー関数にマッピング
3. **バリデーション**: フォームでデータの正当性をチェック
4. **ビジネスロジック**: 在庫チェックなどのルールを適用
5. **ORM**: PythonコードをSQLに変換
6. **データベース**: トランザクションでデータを安全に保存
7. **レスポンス**: 成功メッセージと共にリダイレクト
8. **フィードバック**: ユーザーに結果を表示

### 面接でのアピールポイント

- **多層防御**: フォーム、ビュー、データベースの各層でバリデーション
- **トランザクション管理**: データ整合性を保証
- **セキュリティ**: CSRF、SQLインジェクション、XSS対策を実装
- **パフォーマンス**: N+1問題の回避、インデックスの活用
- **エラーハンドリング**: 適切なエラーメッセージとロールバック

### 次のステップ（改善案）

- REST APIの実装（Django REST Framework）
- 非同期処理（Celery）でメール通知
- キャッシング（Redis）でパフォーマンス向上
- ロギングとモニタリング（Sentry）
