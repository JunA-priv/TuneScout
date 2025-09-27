#!/usr/bin/env python3
"""基本的な動作テスト"""

import asyncio
import sys
from packages.common.settings import settings
from packages.common.db import supabase

async def test_supabase_connection():
    """Supabase接続テスト"""
    try:
        if supabase is None:
            print("❌ Supabase接続: クライアントが初期化されていません")
            return False
        # 簡単なクエリでテスト
        result = supabase.table('user_profiles').select('*').limit(1).execute()
        print("✅ Supabase接続: OK")
        return True
    except Exception as e:
        print(f"❌ Supabase接続: エラー - {e}")
        return False

def test_spotify_credentials():
    """Spotify API認証情報テスト"""
    if settings.spotify_client_id and settings.spotify_client_secret:
        print("✅ Spotify認証情報: OK")
        return True
    else:
        print("❌ Spotify認証情報: 未設定")
        return False

def test_settings():
    """設定値テスト"""
    print(f"Database URL: {settings.database_url}")
    print(f"Supabase URL: {settings.supabase_url}")
    print(f"Redis URL: {settings.redis_url}")
    print(f"Spotify Client ID: {settings.spotify_client_id[:10]}..." if settings.spotify_client_id else "未設定")
    return True

async def main():
    print("=== TuneScout 基本動作テスト ===\n")
    
    # 設定値確認
    print("1. 設定値確認")
    test_settings()
    print()
    
    # Spotify認証情報確認
    print("2. Spotify認証情報確認")
    spotify_ok = test_spotify_credentials()
    print()
    
    # Supabase接続確認
    print("3. Supabase接続確認")
    supabase_ok = await test_supabase_connection()
    print()
    
    # 結果サマリー
    print("=== テスト結果 ===")
    if spotify_ok and supabase_ok:
        print("✅ 全てのテストが成功しました")
        return 0
    else:
        print("❌ 一部のテストが失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))