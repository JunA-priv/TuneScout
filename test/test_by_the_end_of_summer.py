#!/usr/bin/env python3
"""by the end of summer全関連アーティストCSV出力"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def test_by_the_end_of_summer():
    """by the end of summerの全関連アーティストをCSV出力"""
    client = SpotifyClient()
    
    artists = await client.search_artists_by_name("by the end of summer")
    if not artists:
        print("by the end of summerが見つかりません")
        return
    
    artist = artists[0]
    print(f"=== {artist['name']} (人気度: {artist['popularity']}) ===")
    print(f"ジャンル: {artist.get('genres', [])}")
    
    all_related = await client.dig_related_artists([artist], depth_limit=2)
    print(f"関連アーティスト総数: {len(all_related)}")
    
    # 全関連アーティストをCSV出力
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"by_the_end_of_summer_all_{timestamp}.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'name', 'popularity', 'genres', 'followers', 'parent_id', 'parent_name', 'depth']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for related in all_related:
            writer.writerow({
                'id': related['id'],
                'name': related['name'],
                'popularity': related['popularity'],
                'genres': ', '.join(related.get('genres', [])),
                'followers': related.get('followers', {}).get('total', 0),
                'parent_id': related['parent_id'],
                'parent_name': related['parent_name'],
                'depth': related.get('depth', 1)
            })
    
    print(f"全関連アーティストCSV出力完了: {csv_file}")
    
    # 条件合致数も表示
    filtered_count = 0
    for related in all_related:
        popularity = related.get('popularity', 0)
        genres = [g.lower() for g in related.get('genres', [])]
        
        if 1 <= popularity <= 40:
            has_match = any(keyword in ' '.join(genres) for keyword in 
                          ['japanese indie', 'math rock', 'j-rock', 'midwest emo', 'indie'])
            if has_match:
                filtered_count += 1
    
    print(f"条件合致アーティスト数: {filtered_count}")

if __name__ == "__main__":
    asyncio.run(test_by_the_end_of_summer())