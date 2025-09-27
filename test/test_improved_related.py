#!/usr/bin/env python3
"""改良された関連アーティスト検索テスト"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient
from packages.common.db import supabase

async def test_improved_related():
    """改良された関連アーティスト検索をテスト"""
    client = SpotifyClient()
    
    # テスト用アーティスト（ジャンル情報があるもの）
    test_artists = ["tricot", "toe", "LITE"]
    
    for artist_name in test_artists:
        print(f"\n=== {artist_name}を検索中 ===")
        artists = await client.search_artists_by_name(artist_name)
        
        if not artists:
            print(f"{artist_name}が見つかりません")
            continue
        
        artist = artists[0]
        print(f"見つかりました: {artist['name']} (人気度: {artist['popularity']})")
        print(f"ジャンル: {artist.get('genres', [])}")
        
        # 関連アーティストを取得（ジャンル検索含む）
        print("関連アーティスト取得中...")
        related_artists = await client.get_related_artists(artist['id'])
        print(f"関連アーティスト数: {len(related_artists)}")
        
        if related_artists:
            # 条件フィルタリング
            filtered_artists = []
            for related in related_artists:
                popularity = related.get('popularity', 0)
                genres = [g.lower() for g in related.get('genres', [])]
                
                # 人気度2-24の条件
                if 2 <= popularity <= 24:
                    # ジャンル条件
                    has_japanese_indie = "japanese indie" in genres
                    has_math_midwest = "math rock" in genres and "midwest emo" in genres
                    has_math_rock = "math rock" in genres
                    has_post_rock = "post rock" in genres
                    
                    if has_japanese_indie or has_math_midwest or has_math_rock or has_post_rock:
                        related['parent_id'] = artist['id']
                        related['parent_name'] = artist['name']
                        filtered_artists.append(related)
            
            print(f"条件合致アーティスト: {len(filtered_artists)}")
            
            if filtered_artists:
                # CSV出力
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_file = f"{artist_name}_filtered_{timestamp}.csv"
                
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['id', 'name', 'popularity', 'genres', 'followers', 'parent_id', 'parent_name']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for filtered in filtered_artists:
                        writer.writerow({
                            'id': filtered['id'],
                            'name': filtered['name'],
                            'popularity': filtered['popularity'],
                            'genres': ', '.join(filtered.get('genres', [])),
                            'followers': filtered.get('followers', {}).get('total', 0),
                            'parent_id': filtered['parent_id'],
                            'parent_name': filtered['parent_name']
                        })
                
                print(f"CSV出力: {csv_file}")
                
                # 上位3件を表示
                for filtered in filtered_artists[:3]:
                    print(f"  ✓ {filtered['name']} (人気度: {filtered['popularity']}, ジャンル: {filtered.get('genres', [])})")
                
                # Supabaseに登録
                print("Supabase登録中...")
                for filtered in filtered_artists[:3]:  # 最初の3件のみ
                    try:
                        result = supabase.table('artists').upsert({
                            'spotify_id': filtered['id'],
                            'name': filtered['name'],
                            'popularity': filtered['popularity'],
                            'genres': filtered.get('genres', []),
                            'followers': filtered.get('followers', {}).get('total', 0),
                            'parent_artist_id': filtered['parent_id'],
                            'discovery_method': 'related_artist'
                        }).execute()
                        print(f"✓ {filtered['name']} 登録完了")
                    except Exception as e:
                        print(f"✗ {filtered['name']} 登録エラー: {e}")
                
                break  # 最初に成功したアーティストで終了

if __name__ == "__main__":
    asyncio.run(test_improved_related())