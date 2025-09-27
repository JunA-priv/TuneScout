#!/usr/bin/env python3
"""人気アーティストの関連アーティスト取得テスト"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def test_popular_artist_related():
    """人気アーティストから関連アーティストを取得"""
    client = SpotifyClient()
    
    # テスト用アーティスト（関連アーティストが多そうなもの）
    test_artists = ["米津玄師", "あいみょん", "King Gnu"]
    
    for artist_name in test_artists:
        print(f"\n=== {artist_name}を検索中 ===")
        artists = await client.search_artists_by_name(artist_name)
        
        if not artists:
            print(f"{artist_name}が見つかりません")
            continue
        
        artist = artists[0]
        print(f"見つかりました: {artist['name']} (人気度: {artist['popularity']})")
        
        # 関連アーティストを1階層だけ取得
        print("関連アーティスト取得中...")
        related_artists = await client.get_related_artists(artist['id'])
        print(f"関連アーティスト数: {len(related_artists)}")
        
        if related_artists:
            # CSV出力
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = f"{artist_name}_related_{timestamp}.csv"
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['id', 'name', 'popularity', 'genres', 'followers']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for related in related_artists[:10]:  # 上位10件
                    writer.writerow({
                        'id': related['id'],
                        'name': related['name'],
                        'popularity': related['popularity'],
                        'genres': ', '.join(related.get('genres', [])),
                        'followers': related.get('followers', {}).get('total', 0)
                    })
            
            print(f"CSV出力: {csv_file}")
            
            # 条件合致チェック
            filtered = []
            for related in related_artists:
                popularity = related.get('popularity', 0)
                genres = [g.lower() for g in related.get('genres', [])]
                
                if 2 <= popularity <= 24:
                    has_japanese_indie = "japanese indie" in genres
                    has_math_midwest = "math rock" in genres and "midwest emo" in genres
                    
                    if has_japanese_indie or has_math_midwest:
                        filtered.append(related)
            
            print(f"条件合致アーティスト: {len(filtered)}")
            for f in filtered[:5]:
                print(f"  - {f['name']} (人気度: {f['popularity']})")
            
            break  # 最初に成功したアーティストで終了

if __name__ == "__main__":
    asyncio.run(test_popular_artist_related())