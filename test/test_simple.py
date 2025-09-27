#!/usr/bin/env python3
"""シンプルテスト"""

import asyncio
import sys
import os
import httpx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.etl.sources.spotify import SpotifyClient

async def test_simple():
    """シンプルな検索テスト"""
    client = SpotifyClient()
    await client.get_access_token()
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {client.access_token}"},
            params={"q": "genre:indie", "type": "album", "market": "JP", "limit": 20}
        )
        
        albums = response.json().get("albums", {}).get("items", [])
        print(f"取得アルバム数: {len(albums)}")
        
        found_count = 0
        for album in albums:
            for artist in album.get("artists", []):
                try:
                    artist_info = await client.get_artist_info(artist["id"])
                    popularity = artist_info.get("popularity", 0)
                    
                    if 3 <= popularity <= 24:
                        print(f"✓ {artist_info['name']} - {album['name']} (人気度: {popularity})")
                        found_count += 1
                        
                except Exception:
                    continue
        
        print(f"条件合致: {found_count}件")

if __name__ == "__main__":
    asyncio.run(test_simple())