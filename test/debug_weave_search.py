#!/usr/bin/env python3
"""weave検索結果詳細確認"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def debug_weave_search():
    """weaveの検索結果を詳細確認"""
    client = SpotifyClient()
    
    # 通常検索
    artists = await client.search_artists_by_name("weave")
    print(f"通常検索結果: {len(artists)}件")
    
    for i, artist in enumerate(artists[:10]):
        print(f"{i+1}. {artist['name']} (人気度: {artist['popularity']}, ジャンル: {artist.get('genres', [])})")
    
    # ジャンル指定検索
    if not client.access_token:
        await client.get_access_token()
    
    import httpx
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {client.access_token}"},
            params={"q": "weave genre:japanese indie", "type": "artist", "limit": 10}
        )
        
        if response.status_code == 200:
            data = response.json()
            artists = data.get("artists", {}).get("items", [])
            print(f"\nジャンル指定検索結果: {len(artists)}件")
            
            for i, artist in enumerate(artists):
                print(f"{i+1}. {artist['name']} (人気度: {artist['popularity']}, ジャンル: {artist.get('genres', [])})")

if __name__ == "__main__":
    asyncio.run(debug_weave_search())