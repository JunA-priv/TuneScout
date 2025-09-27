#!/usr/bin/env python3
"""Supabase DB接続テスト（パスワード不要）"""

from packages.common.db import supabase, supabase_admin
from packages.common.settings import settings

def test_supabase_tables():
    """Supabaseテーブル存在確認"""
    try:
        # user_profilesテーブル確認
        result = supabase.table('user_profiles').select('*').limit(1).execute()
        print(f"✅ user_profiles: {len(result.data)}件")
        
        # artistsテーブル確認（存在しない場合はエラー）
        try:
            result = supabase.table('artists').select('*').limit(1).execute()
            print(f"✅ artists: {len(result.data)}件")
        except Exception as e:
            print(f"❌ artists テーブルが存在しません: {e}")
            
        # albumsテーブル確認
        try:
            result = supabase.table('albums').select('*').limit(1).execute()
            print(f"✅ albums: {len(result.data)}件")
        except Exception as e:
            print(f"❌ albums テーブルが存在しません: {e}")
            
        return True
    except Exception as e:
        print(f"❌ Supabaseテーブル確認エラー: {e}")
        return False

def create_sample_data():
    """サンプルデータ作成"""
    try:
        if supabase_admin is None:
            print("❌ Supabase adminクライアントが利用できません")
            return False
            
        # サンプルアーティストデータ
        sample_artist = {
            "id": "test_artist_1",
            "name": "テストアーティスト",
            "popularity": 25,
            "genres": ["j-pop", "indie"],
            "followers": 1000,
            "spotify_url": "https://open.spotify.com/artist/test"
        }
        
        result = supabase_admin.table('artists').insert(sample_artist).execute()
        print("✅ サンプルアーティストデータ作成成功")
        
        # サンプルアルバムデータ
        sample_album = {
            "id": "test_album_1",
            "name": "テストアルバム",
            "artist_id": "test_artist_1",
            "release_date": "2024-01-01",
            "total_tracks": 10,
            "spotify_url": "https://open.spotify.com/album/test"
        }
        
        result = supabase_admin.table('albums').insert(sample_album).execute()
        print("✅ サンプルアルバムデータ作成成功")
        
        return True
    except Exception as e:
        print(f"❌ サンプルデータ作成エラー: {e}")
        return False

if __name__ == "__main__":
    print("=== Supabase DB接続テスト ===\n")
    
    print("1. 設定確認")
    print(f"Supabase URL: {settings.supabase_url}")
    print(f"プロジェクトID: yemnpjwjzuufwdvsvflm")
    print()
    
    print("2. テーブル確認")
    test_supabase_tables()
    print()
    
    print("3. サンプルデータ作成（テーブルが存在する場合）")
    create_sample_data()
    print()
    
    print("=== 次のステップ ===")
    print("1. Supabaseダッシュボードでテーブルを作成")
    print("2. SQL Editorで supabase_schema.sql を実行")
    print("3. DATABASE_URLにパスワードを設定（SQLAlchemy用）")