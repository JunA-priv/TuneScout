#!/usr/bin/env python3
"""機能テスト"""

import asyncio
import httpx

API_BASE_URL = "http://localhost:8000"

async def test_auth_endpoints():
    """認証エンドポイントテスト"""
    async with httpx.AsyncClient() as client:
        # ユーザー登録テスト（エラーレスポンスの確認）
        try:
            response = await client.post(f"{API_BASE_URL}/auth/register", 
                json={"email": "test@example.com", "password": "testpass"})
            print(f"✅ 認証登録エンドポイント: {response.status_code}")
        except Exception as e:
            print(f"❌ 認証登録エンドポイント: {e}")

async def test_recommendations():
    """レコメンドエンドポイントテスト"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/recommendations/today")
            print(f"✅ 本日のレコメンド: {response.status_code}")
        except Exception as e:
            print(f"❌ 本日のレコメンド: {e}")

async def test_spotify_integration():
    """Spotify統合テスト"""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials
        from packages.common.settings import settings
        
        client_credentials_manager = SpotifyClientCredentials(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
        # 簡単な検索テスト
        results = sp.search(q='artist:Yoasobi', type='artist', limit=1)
        if results['artists']['items']:
            print("✅ Spotify API接続: OK")
            return True
        else:
            print("❌ Spotify API: 検索結果なし")
            return False
    except Exception as e:
        print(f"❌ Spotify API: {e}")
        return False

async def main():
    print("=== TuneScout 機能テスト ===\n")
    
    print("1. 認証エンドポイント")
    await test_auth_endpoints()
    print()
    
    print("2. レコメンドエンドポイント")
    await test_recommendations()
    print()
    
    print("3. Spotify API統合")
    await test_spotify_integration()
    print()

if __name__ == "__main__":
    asyncio.run(main())