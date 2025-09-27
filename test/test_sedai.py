#!/usr/bin/env python3
"""せだい関連アーティスト取得テスト"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def test_sedai():
    """せだいから関連アーティストを取得"""
    client = SpotifyClient()
    
    artists = await client.search_artists_by_name("せだい")
    if not artists:
        print("せだいが見つかりません")
        return
    
    sedai = artists[0]
    print(f"=== {sedai['name']} (人気度: {sedai['popularity']}) ===")
    print(f"ジャンル: {sedai.get('genres', [])}")
    
    all_related = await client.dig_related_artists([sedai], depth_limit=2)
    print(f"関連アーティスト総数: {len(all_related)}")
    
    # 条件フィルタリング
    filtered_artists = []
    for artist in all_related:
        popularity = artist.get('popularity', 0)
        genres = [g.lower() for g in artist.get('genres', [])]
        
        if 1 <= popularity <= 30:
            has_match = any(keyword in ' '.join(genres) for keyword in 
                          ['japanese indie', 'math rock', 'j-rock', 'midwest emo', 'post rock'])
            
            if has_match:
                filtered_artists.append(artist)
                print(f"✓ {artist['name']} (人気度: {popularity}, ジャンル: {artist.get('genres', [])})")
    
    print(f"\n条件合致アーティスト: {len(filtered_artists)}")
    
    if filtered_artists:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"sedai_related_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'name', 'popularity', 'genres', 'followers', 'parent_name']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for artist in filtered_artists:
                writer.writerow({
                    'id': artist['id'],
                    'name': artist['name'],
                    'popularity': artist['popularity'],
                    'genres': ', '.join(artist.get('genres', [])),
                    'followers': artist.get('followers', {}).get('total', 0),
                    'parent_name': artist['parent_name']
                })
        
        print(f"CSV出力完了: {csv_file}")

if __name__ == "__main__":
    asyncio.run(test_sedai())