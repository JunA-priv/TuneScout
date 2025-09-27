#!/usr/bin/env python3
"""ANORAK!の関連アーティスト取得テスト"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient
from packages.common.db import supabase

async def test_anorak_related():
    """ANORAK!から関連アーティストを取得してテスト"""
    client = SpotifyClient()
    
    # 1. ANORAK!を検索
    print("=== ANORAK!を検索中 ===")
    artists = await client.search_artists_by_name("ANORAK!")
    
    if not artists:
        print("ANORAK!が見つかりません")
        return
    
    anorak = artists[0]
    print(f"見つかりました: {anorak['name']} (人気度: {anorak['popularity']})")
    
    # 2. 関連アーティストを再帰的に取得
    print("\n=== 関連アーティスト取得中 ===")
    related_artists = await client.dig_related_artists([anorak], depth_limit=3)
    print(f"関連アーティスト総数: {len(related_artists)}")
    
    # 3. 条件フィルタリング
    print("\n=== 条件フィルタリング ===")
    filtered_artists = []
    
    for artist in related_artists:
        popularity = artist.get('popularity', 0)
        genres = [g.lower() for g in artist.get('genres', [])]
        
        # 人気度2-24の条件
        if not (2 <= popularity <= 24):
            continue
            
        # ジャンル条件
        has_japanese_indie = "japanese indie" in genres
        has_math_midwest = "math rock" in genres and "midwest emo" in genres
        
        if has_japanese_indie or has_math_midwest:
            artist['genre_match'] = 'japanese indie' if has_japanese_indie else 'math rock + midwest emo'
            filtered_artists.append(artist)
    
    print(f"条件合致アーティスト: {len(filtered_artists)}")
    
    # 4. CSV出力
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"anorak_related_{timestamp}.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if filtered_artists:
            fieldnames = ['id', 'name', 'popularity', 'genres', 'followers', 'parent_id', 'parent_name', 'genre_match']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for artist in filtered_artists:
                writer.writerow({
                    'id': artist['id'],
                    'name': artist['name'],
                    'popularity': artist['popularity'],
                    'genres': ', '.join(artist.get('genres', [])),
                    'followers': artist.get('followers', {}).get('total', 0),
                    'parent_id': artist['parent_id'],
                    'parent_name': artist['parent_name'],
                    'genre_match': artist['genre_match']
                })
    
    print(f"CSV出力完了: {csv_file}")
    
    # 5. Supabaseに登録
    if filtered_artists:
        print("\n=== Supabase登録中 ===")
        for artist in filtered_artists:
            try:
                result = supabase.table('artists').upsert({
                    'spotify_id': artist['id'],
                    'name': artist['name'],
                    'popularity': artist['popularity'],
                    'genres': artist.get('genres', []),
                    'followers': artist.get('followers', {}).get('total', 0),
                    'parent_artist_id': artist['parent_id'],
                    'discovery_method': 'related_artist'
                }).execute()
                print(f"✓ {artist['name']} 登録完了")
            except Exception as e:
                print(f"✗ {artist['name']} 登録エラー: {e}")
    
    print(f"\n=== 完了 ===")
    print(f"総取得数: {len(related_artists)}")
    print(f"条件合致数: {len(filtered_artists)}")
    print(f"CSV: {csv_file}")

if __name__ == "__main__":
    asyncio.run(test_anorak_related())