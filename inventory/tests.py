import threading
import time

from django.db import transaction
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import InventoryItem, Rental
from datetime import date, timedelta


class RentalTestCase(TestCase):
    """貸出・返却機能のテストケース"""
    
    def setUp(self):
        """テスト用のデータをセットアップ"""
        # テストユーザーを作成
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.admin_user = User.objects.create_user(username='admin', password='adminpass123', is_staff=True)
        
        # テスト用の備品を作成
        self.item = InventoryItem.objects.create(
            name='テスト備品',
            category='電子機器',
            quantity=10,
            is_available=True,
            added_by=self.user
        )
        
        self.client = Client()
    
    def test_rental_decreases_stock(self):
        """テスト1: 貸出機能：在庫が正しく減る"""
        self.client.login(username='testuser', password='testpass123')
        
        # 貸出前の在庫数を確認
        initial_quantity = self.item.quantity
        
        # 3個貸し出す
        response = self.client.post(reverse('rental_create', args=[self.item.id]), {
            'quantity': 3,
            'expected_return_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        })
        
        # 在庫が減ったか確認
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, initial_quantity - 3)
    
    def test_rental_prevents_overselling(self):
        """テスト2: 貸出機能：在庫不足のチェック"""
        self.client.login(username='testuser', password='testpass123')
        
        # 在庫以上の数量を借りようとする
        response = self.client.post(reverse('rental_create', args=[self.item.id]), {
            'quantity': 100,  # 在庫は10個なので100個は借りられない
            'expected_return_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
        }, follow=True)
        
        # リダイレクトされることを確認
        self.assertEqual(response.status_code, 200)
        
        # 在庫が減っていないことを確認
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 10)
    
    def test_return_increases_stock(self):
        """テスト3: 返却機能：在庫が正しく増え、ステータスが更新される"""
        self.client.login(username='testuser', password='testpass123')
        
        # 先に貸出を実行（1個だけ借りる）
        rental = Rental.objects.create(
            item=self.item,
            user=self.user,
            quantity=1,  # 1個だけ借りる（全て返却するとstatusがreturnedになる）
            status='borrowed',
            rental_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7)
        )
        self.item.quantity -= 1
        self.item.save()
        
        initial_quantity = self.item.quantity
        
        # 返却を実行
        response = self.client.post(reverse('return_item', args=[rental.id]))
        
        # ステータスが更新されたか確認（1個全て返却したのでreturnedになる）
        rental.refresh_from_db()
        self.assertEqual(rental.status, 'returned')
        self.assertEqual(rental.quantity, 0)
        
        # 在庫が増えたか確認
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, initial_quantity + 1)


class PermissionTestCase(TestCase):
    """権限チェックのテストケース"""
    
    def setUp(self):
        """テスト用のユーザーをセットアップ"""
        self.general_user = User.objects.create_user(username='generaluser', password='testpass123')
        self.admin_user = User.objects.create_user(username='adminuser', password='adminpass123', is_staff=True)
        self.client = Client()
    
    def test_admin_only_access(self):
        """テスト4: 権限チェック：管理者のみアクセス可能"""
        # 一般ユーザーでログイン
        self.client.login(username='generaluser', password='testpass123')
        
        # 管理者ダッシュボードにアクセス
        response = self.client.get(reverse('admin_dashboard'))
        
        # アクセスが拒否されることを確認（302リダイレクトまたは403エラー）
        self.assertIn(response.status_code, [302, 403])
        
        # 管理者でログイン
        self.client.login(username='adminuser', password='adminpass123')
        response = self.client.get(reverse('admin_dashboard'))
        
        # 管理者はアクセス可能
        self.assertEqual(response.status_code, 200)
    
    def test_login_required(self):
        """テスト5: 認証チェック：未ログインユーザーを弾く"""
        # ログインせずにダッシュボードにアクセス
        response = self.client.get(reverse('user_dashboard'))

        # ログインページにリダイレクトされることを確認
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class InventoryItemLockingTestCase(TransactionTestCase):
    """rental_create が在庫更新の排他制御に使っている
    select_for_update() が、実際にDBレベルで行ロックとして
    機能することを検証するテスト。

    2つのスレッドでそれぞれ別トランザクションを開始し、
    threading.Event で「先行トランザクションがロックを取得した
    タイミング」「後続トランザクションが読み取りを試みるタイミング」
    を明示的に同期させることで、タイミング依存のない確実な検証を行う。

    先行トランザクションが select_for_update() でロックを保持した
    まま quantity=0 に更新してコミットするまで、後続トランザクションの
    select_for_update() はブロックされ、コミット後の最新値(0)を
    読み取れることを確認する。ここで select_for_update() を外すと、
    後続の読み取りはロックされずコミット前の古い値(1)を読んでしまい、
    rental_create の在庫チェックが古い在庫数に基づいて行われる
    (＝同時貸出でオーバーセルが起こる)ことになる。
    """

    def setUp(self):
        self.user = User.objects.create_user(username='locker', password='testpass123')
        self.item = InventoryItem.objects.create(
            name='ロックテスト用備品',
            category='テスト',
            quantity=1,
            is_available=True,
            added_by=self.user,
        )

    def test_select_for_update_blocks_until_holder_commits(self):
        holder_has_lock = threading.Event()
        release_holder = threading.Event()
        second_read = {}

        def holder():
            with transaction.atomic():
                item = InventoryItem.objects.select_for_update().get(pk=self.item.pk)
                holder_has_lock.set()
                release_holder.wait(timeout=5)
                item.quantity = 0
                item.save()
            # ここでコミットされ、行ロックが解放される

        def waiter():
            holder_has_lock.wait(timeout=5)
            with transaction.atomic():
                item = InventoryItem.objects.select_for_update().get(pk=self.item.pk)
                second_read['quantity'] = item.quantity

        t1 = threading.Thread(target=holder)
        t2 = threading.Thread(target=waiter)

        t1.start()
        self.assertTrue(holder_has_lock.wait(timeout=5), "holderがロックを取得できなかった")

        t2.start()
        # t2 が select_for_update() の行ロック待ちでブロックされる猶予を与える
        time.sleep(0.3)
        release_holder.set()

        t1.join(timeout=5)
        t2.join(timeout=5)

        # select_for_update が効いていれば、t2 は holder のコミット後の
        # 最新値(0)しか読めない(古い値の1を読めてしまってはいけない)
        self.assertEqual(second_read.get('quantity'), 0)

