#!/usr/bin/env python3
"""関連アーティストAPI直接テスト"""

import asyncio
import httpx
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def debug_related_api():
    """関連アーティストAPIを直接テスト"""
    client = SpotifyClient()
    token = await client.get_access_token()
    
    # テスト用アーティストID（King Gnu）
    artist_id = "6wxfx1yhyqjCPYwwxJktR2"
    
    async with httpx.AsyncClient() as http_client:
        # 1. アーティスト情報取得
        print("=== アーティスト情報 ===")
        response = await http_client.get(
            f"https://api.spotify.com/v1/artists/{artist_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"ステータス: {response.status_code}")
        if response.status_code == 200:
            artist = response.json()
            print(f"名前: {artist['name']}")
            print(f"人気度: {artist['popularity']}")
            print(f"市場: {artist.get('available_markets', [])[:5]}")
        
        # 2. 関連アーティスト取得
        print("\n=== 関連アーティスト ===")
        response = await http_client.get(
            f"https://api.spotify.com/v1/artists/{artist_id}/related-artists",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"ステータス: {response.status_code}")
        print(f"レスポンス: {response.text[:200]}")
        
        if response.status_code == 200:
            data = response.json()
            artists = data.get('artists', [])
            print(f"関連アーティスト数: {len(artists)}")
            for artist in artists[:3]:
                print(f"  - {artist['name']} (人気度: {artist['popularity']})")

if __name__ == "__main__":
    asyncio.run(debug_related_api())