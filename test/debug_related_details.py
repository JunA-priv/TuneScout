#!/usr/bin/env python3
"""関連アーティストの詳細確認"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def debug_related_details():
    """関連アーティストの詳細を確認"""
    client = SpotifyClient()
    
    # tricotの関連アーティストを詳細確認
    artists = await client.search_artists_by_name("tricot")
    if not artists:
        return
        
    tricot = artists[0]
    print(f"=== {tricot['name']} ===")
    print(f"人気度: {tricot['popularity']}")
    print(f"ジャンル: {tricot.get('genres', [])}")
    
    related_artists = await client.get_related_artists(tricot['id'])
    print(f"\n関連アーティスト数: {len(related_artists)}")
    
    for i, artist in enumerate(related_artists):
        popularity = artist.get('popularity', 0)
        genres = artist.get('genres', [])
        followers = artist.get('followers', {}).get('total', 0)
        
        print(f"\n{i+1}. {artist['name']}")
        print(f"   人気度: {popularity}")
        print(f"   ジャンル: {genres}")
        print(f"   フォロワー: {followers:,}")
        
        # 条件チェック
        genre_match = []
        genres_lower = [g.lower() for g in genres]
        if "japanese indie" in genres_lower:
            genre_match.append("japanese indie")
        if "math rock" in genres_lower:
            genre_match.append("math rock")
        if "midwest emo" in genres_lower:
            genre_match.append("midwest emo")
        if "post rock" in genres_lower:
            genre_match.append("post rock")
            
        if genre_match:
            print(f"   ✓ ジャンル合致: {genre_match}")
        
        if 2 <= popularity <= 50:  # 条件を緩和
            print(f"   ✓ 人気度範囲内 (2-50)")

if __name__ == "__main__":
    asyncio.run(debug_related_details())