#!/usr/bin/env python3
"""せだい検索結果詳細確認"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def debug_sedai():
    """せだいの検索結果を詳細確認"""
    client = SpotifyClient()
    
    # せだいで検索（複数結果を確認）
    artists = await client.search_artists_by_name("せだい")
    print(f"検索結果数: {len(artists)}")
    
    for i, artist in enumerate(artists[:5]):  # 上位5件
        print(f"\n{i+1}. {artist['name']}")
        print(f"   人気度: {artist['popularity']}")
        print(f"   ジャンル: {artist.get('genres', [])}")
        print(f"   ID: {artist['id']}")
        
        # 関連アーティスト確認
        related = await client.get_related_artists(artist['id'])
        print(f"   関連アーティスト数: {len(related)}")
        
        for j, rel in enumerate(related[:3]):  # 上位3件
            print(f"     - {rel['name']} (人気度: {rel['popularity']})")

if __name__ == "__main__":
    asyncio.run(debug_sedai())