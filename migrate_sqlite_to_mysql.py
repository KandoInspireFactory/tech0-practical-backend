# backend/db_control/migrate_sqlite_to_mysql.py
"""
SQLiteからMySQLへのデータ移行スクリプト
"""
import platform
print("platform:", platform.uname())

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

# SQLite接続
from db_control.connect import engine as sqlite_engine
from db_control.mymodels import (
    Base as SQLiteBase,
    Customers as SQLiteCustomers,
    Items as SQLiteItems,
    Purchases as SQLitePurchases,
    PurchaseDetails as SQLitePurchaseDetails
)

# MySQL接続
from db_control.connect_MySQL import engine as mysql_engine
from db_control.mymodels_MySQL import (
    Base as MySQLBase,
    Customers as MySQLCustomers,
    Items as MySQLItems,
    Purchases as MySQLPurchases,
    PurchaseDetails as MySQLPurchaseDetails
)

# SQLite接続の確認
print("=" * 50)
print("SQLite接続を確認中...")
print(f"SQLite engine: {sqlite_engine}")
print(f"SQLite URL: {sqlite_engine.url}")

# テーブル一覧を確認
from sqlalchemy import inspect
inspector = inspect(sqlite_engine)
tables = inspector.get_table_names()
print(f"SQLiteテーブル: {tables}")

# 直接SQLでデータ数を確認
try:
    with sqlite_engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM customers"))
        count = result.scalar()
        print(f"直接SQLカウント: {count}")
except Exception as e:
    print(f"カウント確認エラー: {e}")

print("=" * 50)


def migrate_customers():
    """Customersテーブルのデータを移行"""
    print("Customersを移行中...")
    
    # SQLiteセッション（check_sqlite_data.pyと同じ方法）
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    # MySQLセッション
    MySQLSession = sessionmaker(bind=mysql_engine)
    mysql_session = MySQLSession()
    
    try:
        # check_sqlite_data.pyと同じクエリ方法を使用
        sqlite_customers = sqlite_session.query(SQLiteCustomers).all()
        print(f"  SQLiteで{len(sqlite_customers)}件の顧客を発見")
        
        # デバッグ出力
        for customer in sqlite_customers:
            print(f"    - {customer.customer_id}: {customer.customer_name}")
        
        if len(sqlite_customers) == 0:
            print("  ⚠️  移行するデータがありません！")
            return
        
        migrated_count = 0
        skipped_count = 0
        
        for sqlite_customer in sqlite_customers:
            try:
                # 既存データをチェック
                existing = mysql_session.query(MySQLCustomers).filter(
                    MySQLCustomers.customer_id == sqlite_customer.customer_id
                ).first()
                
                if existing:
                    print(f"  ⚠️  顧客 {sqlite_customer.customer_id} は既に存在します。スキップします...")
                    skipped_count += 1
                    continue
                
                # MySQLに挿入
                mysql_customer = MySQLCustomers(
                    customer_id=sqlite_customer.customer_id,
                    customer_name=sqlite_customer.customer_name,
                    age=sqlite_customer.age,
                    gender=sqlite_customer.gender
                )
                mysql_session.add(mysql_customer)
                mysql_session.commit()
                migrated_count += 1
                print(f"  ✓ 移行完了: {sqlite_customer.customer_id}")
            except Exception as e:
                mysql_session.rollback()
                print(f"  ✗ 顧客 {sqlite_customer.customer_id} をスキップ: {type(e).__name__}: {e}")
                skipped_count += 1
        
        print(f"  サマリー - 移行: {migrated_count}件, スキップ: {skipped_count}件")
        
    except Exception as e:
        print(f"  ✗ 移行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlite_session.close()
        mysql_session.close()


def migrate_items():
    """Itemsテーブルのデータを移行"""
    print("Itemsを移行中...")
    
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    MySQLSession = sessionmaker(bind=mysql_engine)
    mysql_session = MySQLSession()
    
    try:
        sqlite_items = sqlite_session.query(SQLiteItems).all()
        print(f"  SQLiteで{len(sqlite_items)}件の商品を発見")
        
        if len(sqlite_items) == 0:
            print("  ⚠️  移行するデータがありません！")
            return
        
        migrated_count = 0
        skipped_count = 0
        
        for sqlite_item in sqlite_items:
            try:
                # 既存データをチェック
                existing = mysql_session.query(MySQLItems).filter(
                    MySQLItems.item_id == sqlite_item.item_id
                ).first()
                
                if existing:
                    print(f"  ⚠️  商品 {sqlite_item.item_id} は既に存在します。スキップします...")
                    skipped_count += 1
                    continue
                
                mysql_item = MySQLItems(
                    item_id=sqlite_item.item_id,
                    item_name=sqlite_item.item_name,
                    price=sqlite_item.price
                )
                mysql_session.add(mysql_item)
                mysql_session.commit()
                migrated_count += 1
                print(f"  ✓ 移行完了: {sqlite_item.item_id}")
            except Exception as e:
                mysql_session.rollback()
                print(f"  ✗ 商品 {sqlite_item.item_id} をスキップ: {type(e).__name__}: {e}")
                skipped_count += 1
        
        print(f"  サマリー - 移行: {migrated_count}件, スキップ: {skipped_count}件")
        
    except Exception as e:
        print(f"  ✗ 移行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlite_session.close()
        mysql_session.close()


def migrate_purchases():
    """Purchasesテーブルのデータを移行（構造が異なるため変換が必要）"""
    print("Purchasesを移行中...")
    
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    MySQLSession = sessionmaker(bind=mysql_engine)
    mysql_session = MySQLSession()
    
    try:
        sqlite_purchases = sqlite_session.query(SQLitePurchases).all()
        print(f"  SQLiteで{len(sqlite_purchases)}件の購入を発見")
        
        if len(sqlite_purchases) == 0:
            print("  ⚠️  移行するデータがありません！")
            return
        
        migrated_count = 0
        skipped_count = 0
        
        for sqlite_purchase in sqlite_purchases:
            try:
                # SQLite: purchase_id (int), purchase_name (FK), date (datetime)
                # MySQL: purchase_id (String(10)), customer_id (String(10)), purchase_date (String(10))
                
                # purchase_idを文字列に変換（10文字以内）
                purchase_id_str = str(sqlite_purchase.purchase_id)[:10]
                
                # 既存データをチェック
                existing = mysql_session.query(MySQLPurchases).filter(
                    MySQLPurchases.purchase_id == purchase_id_str
                ).first()
                
                if existing:
                    print(f"  ⚠️  購入 {purchase_id_str} は既に存在します。スキップします...")
                    skipped_count += 1
                    continue
                
                # dateを文字列に変換（YYYY-MM-DD形式）
                if isinstance(sqlite_purchase.date, datetime):
                    purchase_date_str = sqlite_purchase.date.strftime('%Y-%m-%d')
                else:
                    purchase_date_str = str(sqlite_purchase.date)[:10]
                
                # purchase_nameがcustomer_idを指している
                customer_id = sqlite_purchase.purchase_name
                
                mysql_purchase = MySQLPurchases(
                    purchase_id=purchase_id_str,
                    customer_id=customer_id,
                    purchase_date=purchase_date_str
                )
                mysql_session.add(mysql_purchase)
                mysql_session.commit()
                migrated_count += 1
                print(f"  ✓ 移行完了: {purchase_id_str}")
            except Exception as e:
                mysql_session.rollback()
                print(f"  ✗ 購入 {sqlite_purchase.purchase_id} をスキップ: {type(e).__name__}: {e}")
                skipped_count += 1
        
        print(f"  サマリー - 移行: {migrated_count}件, スキップ: {skipped_count}件")
        
    except Exception as e:
        print(f"  ✗ 移行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlite_session.close()
        mysql_session.close()


def migrate_purchase_details():
    """PurchaseDetailsテーブルのデータを移行（構造が異なるため変換が必要）"""
    print("PurchaseDetailsを移行中...")
    
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLiteSession()
    
    MySQLSession = sessionmaker(bind=mysql_engine)
    mysql_session = MySQLSession()
    
    try:
        sqlite_details = sqlite_session.query(SQLitePurchaseDetails).all()
        print(f"  SQLiteで{len(sqlite_details)}件の購入詳細を発見")
        
        if len(sqlite_details) == 0:
            print("  ⚠️  移行するデータがありません！")
            return
        
        migrated_count = 0
        skipped_count = 0
        
        for sqlite_detail in sqlite_details:
            try:
                # SQLite: purchase_id (FK, int), item_name (FK), quantity
                # MySQL: detail_id (String(10)), purchase_id (String(10)), item_id (String(10)), quantity
                
                # detail_idを生成（10文字以内のユニークID）
                detail_id = str(uuid.uuid4())[:10]
                
                # purchase_idを文字列に変換
                purchase_id_str = str(sqlite_detail.purchase_id)[:10]
                
                # item_nameがitem_idを指している
                item_id = sqlite_detail.item_name
                
                mysql_detail = MySQLPurchaseDetails(
                    detail_id=detail_id,
                    purchase_id=purchase_id_str,
                    item_id=item_id,
                    quantity=sqlite_detail.quantity
                )
                mysql_session.add(mysql_detail)
                mysql_session.commit()
                migrated_count += 1
                print(f"  ✓ 移行完了 detail_id: {detail_id}")
            except Exception as e:
                mysql_session.rollback()
                print(f"  ✗ 購入詳細をスキップ: {type(e).__name__}: {e}")
                skipped_count += 1
        
        print(f"  サマリー - 移行: {migrated_count}件, スキップ: {skipped_count}件")
        
    except Exception as e:
        print(f"  ✗ 移行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        sqlite_session.close()
        mysql_session.close()


def migrate_all():
    """全テーブルのデータを移行（外部キー制約を考慮して順序を守る）"""
    print("=" * 50)
    print("SQLiteからMySQLへの移行を開始します...")
    print("=" * 50)
    
    # 外部キー制約を考慮して順序を守る
    # 1. Customers（他のテーブルから参照される）
    migrate_customers()
    
    # 2. Items（他のテーブルから参照される）
    migrate_items()
    
    # 3. Purchases（Customersを参照）
    migrate_purchases()
    
    # 4. PurchaseDetails（PurchasesとItemsを参照）
    migrate_purchase_details()
    
    print("=" * 50)
    print("移行が完了しました！")
    print("=" * 50)


if __name__ == "__main__":
    migrate_all()