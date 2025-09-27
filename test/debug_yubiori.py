#!/usr/bin/env python3
"""yubiori関連アーティスト詳細確認"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def debug_yubiori():
    """yubioriの関連アーティスト詳細確認"""
    client = SpotifyClient()
    
    artists = await client.search_artists_by_name("yubiori")
    yubiori = artists[0]
    print(f"=== {yubiori['name']} ===")
    print(f"人気度: {yubiori['popularity']}")
    print(f"ジャンル: {yubiori.get('genres', [])}")
    
    all_related = await client.dig_related_artists([yubiori], depth_limit=2)
    print(f"\n関連アーティスト総数: {len(all_related)}")
    
    for i, artist in enumerate(all_related):
        popularity = artist.get('popularity', 0)
        genres = artist.get('genres', [])
        
        print(f"\n{i+1}. {artist['name']}")
        print(f"   人気度: {popularity}")
        print(f"   ジャンル: {genres}")
        print(f"   親: {artist.get('parent_name', 'N/A')}")
        
        # 条件チェック
        if 2 <= popularity <= 40:
            genres_str = ' '.join([g.lower() for g in genres])
            matches = []
            for keyword in ['japanese indie', 'math rock', 'midwest emo', 'post rock', 'indie rock', 'j-rock']:
                if keyword in genres_str:
                    matches.append(keyword)
            
            if matches:
                print(f"   ✓ 条件合致: {matches}")

if __name__ == "__main__":
    asyncio.run(debug_yubiori())