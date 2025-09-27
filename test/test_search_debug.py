#!/usr/bin/env python3
"""検索デバッグ用スクリプト"""

import asyncio
import sys
import os
import httpx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.etl.sources.spotify import SpotifyClient

async def debug_search():
    """検索クエリをデバッグ"""
    print("=== 検索クエリデバッグ ===")
    
    client = SpotifyClient()
    await client.get_access_token()
    
    # より広範囲な検索クエリ
    search_queries = [
        "year:2024",
        "genre:indie",
        "genre:rock",
        "tag:new"
    ]
    
    async with httpx.AsyncClient() as http_client:
        for query in search_queries:
            print(f"\n検索クエリ: {query}")
            
            response = await http_client.get(
                "https://api.spotify.com/v1/search",
                headers={"Authorization": f"Bearer {client.access_token}"},
                params={"q": query, "type": "album", "market": "JP", "limit": 5}
            )
            
            if response.status_code == 200:
                albums = response.json().get("albums", {}).get("items", [])
                print(f"取得アルバム数: {len(albums)}")
                
                for album in albums[:3]:
                    print(f"  - {album['name']} ({album.get('release_date', 'N/A')})")
                    
                    for artist in album.get("artists", [])[:1]:
                        try:
                            artist_info = await client.get_artist_info(artist["id"])
                            popularity = artist_info.get("popularity", 0)
                            genres = artist_info.get("genres", [])
                            print(f"    アーティスト: {artist_info['name']} (人気度: {popularity})")
                            print(f"    ジャンル: {genres}")
                        except Exception as e:
                            print(f"    エラー: {e}")
            else:
                print(f"エラー: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(debug_search())