#!/usr/bin/env python3
"""weave全関連アーティスト詳細CSV出力"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def test_weave_detailed():
    """weaveの全関連アーティストを詳細表示・CSV出力"""
    client = SpotifyClient()
    
    artist_id = "2taISFyrsTRanZU09L0zt2"
    weave_artist = await client.get_artist_info(artist_id)
    
    print(f"=== {weave_artist['name']} (人気度: {weave_artist['popularity']}) ===")
    print(f"ジャンル: {weave_artist.get('genres', [])}")
    
    all_related = await client.dig_related_artists([weave_artist], depth_limit=2)
    print(f"関連アーティスト総数: {len(all_related)}")
    
    # 全関連アーティストを詳細表示
    print("\n=== 関連アーティスト詳細 ===")
    for i, related in enumerate(all_related):
        popularity = related.get('popularity', 0)
        genres = related.get('genres', [])
        
        print(f"{i+1}. {related['name']}")
        print(f"   人気度: {popularity}")
        print(f"   ジャンル: {genres}")
        print(f"   親: {related['parent_name']}")
        
        # 条件チェック表示
        genres_lower = [g.lower() for g in genres]
        popularity_match = 1 <= popularity <= 40
        genre_match = any(keyword in ' '.join(genres_lower) for keyword in 
                         ['japanese indie', 'math rock', 'j-rock', 'midwest emo', 'indie'])
        
        print(f"   人気度条件(1-40): {'✓' if popularity_match else '✗'}")
        print(f"   ジャンル条件: {'✓' if genre_match else '✗'}")
        print(f"   総合判定: {'✓ 合致' if popularity_match and genre_match else '✗ 不合致'}")
    
    # CSV出力
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"weave_detailed_{timestamp}.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'name', 'popularity', 'genres', 'followers', 'parent_name', 'popularity_match', 'genre_match', 'overall_match']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for related in all_related:
            popularity = related.get('popularity', 0)
            genres_lower = [g.lower() for g in related.get('genres', [])]
            
            popularity_match = 1 <= popularity <= 40
            genre_match = any(keyword in ' '.join(genres_lower) for keyword in 
                             ['japanese indie', 'math rock', 'j-rock', 'midwest emo', 'indie'])
            
            writer.writerow({
                'id': related['id'],
                'name': related['name'],
                'popularity': popularity,
                'genres': ', '.join(related.get('genres', [])),
                'followers': related.get('followers', {}).get('total', 0),
                'parent_name': related['parent_name'],
                'popularity_match': popularity_match,
                'genre_match': genre_match,
                'overall_match': popularity_match and genre_match
            })
    
    print(f"\n詳細CSV出力完了: {csv_file}")

if __name__ == "__main__":
    asyncio.run(test_weave_detailed())