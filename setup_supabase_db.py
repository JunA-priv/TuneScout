#!/usr/bin/env python3
"""Supabase DB接続設定"""

import os
from packages.common.settings import settings
from packages.common.db import supabase

def get_supabase_db_url():
    """SupabaseプロジェクトからDB接続URLを構築"""
    # Supabase URLからプロジェクトIDを抽出
    project_ref = settings.supabase_url.split('//')[1].split('.')[0]
    
    # Supabase PostgreSQL接続URL
    # 形式: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    db_url = f"postgresql://postgres:[YOUR_DB_PASSWORD]@db.{project_ref}.supabase.co:5432/postgres"
    
    print(f"プロジェクトID: {project_ref}")
    print(f"DB接続URL形式: {db_url}")
    print("\n次の手順でDB接続を設定してください:")
    print("1. Supabaseダッシュボード > Settings > Database")
    print("2. Connection stringをコピー")
    print("3. .envファイルのDATABASE_URLを更新")
    
    return project_ref

def test_supabase_connection():
    """Supabase接続テスト"""
    try:
        if supabase is None:
            print("❌ Supabaseクライアントが初期化されていません")
            return False
            
        # テーブル一覧を取得
        result = supabase.table('user_profiles').select('*').limit(1).execute()
        print("✅ Supabase接続成功")
        print(f"user_profilesテーブル: {len(result.data)}件")
        return True
    except Exception as e:
        print(f"❌ Supabase接続エラー: {e}")
        return False

def setup_database_tables():
    """必要なテーブルをSupabaseに作成"""
    try:
        # SQLスキーマファイルを読み込み
        schema_file = "/home/raric/work/ulmuscraft/TuneScout/supabase_schema.sql"
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            print("✅ スキーマファイル読み込み完了")
            print("次のSQLをSupabaseのSQL Editorで実行してください:")
            print("=" * 50)
            print(schema_sql)
            print("=" * 50)
        else:
            print("❌ supabase_schema.sqlが見つかりません")
    except Exception as e:
        print(f"❌ スキーマ読み込みエラー: {e}")

if __name__ == "__main__":
    print("=== Supabase DB接続設定 ===\n")
    
    # プロジェクト情報取得
    project_ref = get_supabase_db_url()
    print()
    
    # 接続テスト
    print("=== 接続テスト ===")
    test_supabase_connection()
    print()
    
    # スキーマ設定
    print("=== データベーススキーマ ===")
    setup_database_tables()