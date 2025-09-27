#!/usr/bin/env python3
"""yubiori関連アーティスト取得テスト"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient
from packages.common.db import supabase

async def test_yubiori():
    """yubioriから関連アーティストを取得"""
    client = SpotifyClient()
    
    # yubioriを検索
    print("=== yubioriを検索中 ===")
    artists = await client.search_artists_by_name("yubiori")
    
    if not artists:
        print("yubioriが見つかりません")
        return
    
    yubiori = artists[0]
    print(f"見つかりました: {yubiori['name']} (人気度: {yubiori['popularity']})")
    print(f"ジャンル: {yubiori.get('genres', [])}")
    
    # 再帰的関連アーティスト取得
    print("\n=== 関連アーティスト取得中 ===")
    all_related = await client.dig_related_artists([yubiori], depth_limit=2)
    print(f"総取得数: {len(all_related)}")
    
    # 条件フィルタリング
    filtered_artists = []
    for artist in all_related:
        popularity = artist.get('popularity', 0)
        genres = [g.lower() for g in artist.get('genres', [])]
        
        if 2 <= popularity <= 40:
            has_match = any(keyword in ' '.join(genres) for keyword in 
                          ['japanese indie', 'math rock', 'midwest emo', 'post rock', 'indie rock', 'j-rock'])
            
            if has_match:
                filtered_artists.append(artist)
                print(f"✓ {artist['name']} (人気度: {popularity})")
    
    print(f"\n条件合致アーティスト: {len(filtered_artists)}")
    
    if filtered_artists:
        # CSV出力
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"yubiori_related_{timestamp}.csv"
        
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
        
        print(f"CSV出力: {csv_file}")
        
        # Supabase登録
        for artist in filtered_artists:
            try:
                supabase.table('artists').upsert({
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

if __name__ == "__main__":
    asyncio.run(test_yubiori())