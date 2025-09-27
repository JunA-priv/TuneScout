#!/usr/bin/env python3
"""せだい全関連アーティストCSV出力"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def test_sedai_all_csv():
    """せだいの全関連アーティストをCSV出力"""
    client = SpotifyClient()
    
    artists = await client.search_artists_by_name("せだい")
    sedai = None
    for artist in artists:
        if 'せだい' in artist['name'].lower():
            sedai = artist
            break
    
    if not sedai:
        print("せだいが見つかりません")
        return
    
    print(f"=== {sedai['name']} (人気度: {sedai['popularity']}) ===")
    
    all_related = await client.dig_related_artists([sedai], depth_limit=2)
    print(f"関連アーティスト総数: {len(all_related)}")
    
    # 全関連アーティストをCSV出力
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"sedai_all_related_{timestamp}.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'name', 'popularity', 'genres', 'followers', 'parent_id', 'parent_name', 'depth']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for artist in all_related:
            writer.writerow({
                'id': artist['id'],
                'name': artist['name'],
                'popularity': artist['popularity'],
                'genres': ', '.join(artist.get('genres', [])),
                'followers': artist.get('followers', {}).get('total', 0),
                'parent_id': artist['parent_id'],
                'parent_name': artist['parent_name'],
                'depth': artist.get('depth', 1)
            })
    
    print(f"全関連アーティストCSV出力完了: {csv_file}")
    
    # 条件合致数も表示
    filtered_count = 0
    for artist in all_related:
        popularity = artist.get('popularity', 0)
        genres = [g.lower() for g in artist.get('genres', [])]
        
        if 1 <= popularity <= 40:
            has_match = any(keyword in ' '.join(genres) for keyword in 
                          ['japanese indie', 'math rock', 'j-rock', 'midwest emo', 'indie'])
            if has_match:
                filtered_count += 1
    
    print(f"条件合致アーティスト数: {filtered_count}")

if __name__ == "__main__":
    asyncio.run(test_sedai_all_csv())