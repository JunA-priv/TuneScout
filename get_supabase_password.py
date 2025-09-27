#!/usr/bin/env python3
"""Supabase DBパスワード取得ガイド"""

print("=== Supabase データベースパスワード取得方法 ===\n")

print("1. Supabaseダッシュボードにアクセス:")
print("   https://supabase.com/dashboard/projects\n")

print("2. プロジェクト 'yemnpjwjzuufwdvsvflm' を選択\n")

print("3. 左サイドバー > Settings > Database\n")

print("4. 'Connection string' セクションで:")
print("   - 'URI' タブを選択")
print("   - パスワードを入力または生成")
print("   - 接続文字列をコピー\n")

print("5. .envファイルのDATABASE_URLを更新:")
print("   例: DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@db.yemnpjwjzuufwdvsvflm.supabase.co:5432/postgres\n")

print("6. または、以下のコマンドで直接設定:")
print("   export DATABASE_URL='postgresql+psycopg://postgres:YOUR_PASSWORD@db.yemnpjwjzuufwdvsvflm.supabase.co:5432/postgres'\n")

print("注意: パスワードは安全に管理してください")