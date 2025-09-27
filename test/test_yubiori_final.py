#!/usr/bin/env python3
"""yubiori最終テスト（条件調整版）"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient
from packages.common.db import supabase

async def test_yubiori_final():
    """yubiori関連アーティスト最終テスト"""
    client = SpotifyClient()
    
    artists = await client.search_artists_by_name("yubiori")
    yubiori = artists[0]
    print(f"=== {yubiori['name']} (人気度: {yubiori['popularity']}) ===")
    
    all_related = await client.dig_related_artists([yubiori], depth_limit=2)
    print(f"関連アーティスト総数: {len(all_related)}")
    
    # 条件フィルタリング（調整版）
    filtered_artists = []
    for artist in all_related:
        popularity = artist.get('popularity', 0)
        genres = [g.lower() for g in artist.get('genres', [])]
        
        # 人気度1-30に調整（Ircleが人気度1で条件に合うため）
        if 1 <= popularity <= 30:
            has_japanese_indie = "japanese indie" in genres
            has_j_rock = "j-rock" in genres
            has_math_rock = "math rock" in genres
            
            if has_japanese_indie or has_j_rock or has_math_rock:
                genre_matches = []
                if has_japanese_indie: genre_matches.append("japanese indie")
                if has_j_rock: genre_matches.append("j-rock")
                if has_math_rock: genre_matches.append("math rock")
                
                artist['genre_match'] = ', '.join(genre_matches)
                filtered_artists.append(artist)
                print(f"✓ {artist['name']} (人気度: {popularity}, ジャンル: {genre_matches})")
    
    print(f"\n条件合致アーティスト: {len(filtered_artists)}")
    
    if filtered_artists:
        # CSV出力
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"yubiori_final_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'name', 'popularity', 'genres', 'followers', 'parent_name', 'genre_match']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for artist in filtered_artists:
                writer.writerow({
                    'id': artist['id'],
                    'name': artist['name'],
                    'popularity': artist['popularity'],
                    'genres': ', '.join(artist.get('genres', [])),
                    'followers': artist.get('followers', {}).get('total', 0),
                    'parent_name': artist['parent_name'],
                    'genre_match': artist['genre_match']
                })
        
        print(f"CSV出力完了: {csv_file}")
        
        # Supabase登録
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
    print(f"総取得数: {len(all_related)}")
    print(f"条件合致数: {len(filtered_artists)}")

if __name__ == "__main__":
    asyncio.run(test_yubiori_final())