#!/usr/bin/env python3
"""ANORAK!再帰的関連アーティスト取得テスト"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient
from packages.common.db import supabase

async def test_anorak_recursive():
    """ANORAK!から再帰的に関連アーティストを取得"""
    client = SpotifyClient()
    
    # ANORAK!を検索
    print("=== ANORAK!を検索中 ===")
    artists = await client.search_artists_by_name("ANORAK!")
    
    if not artists:
        print("ANORAK!が見つかりません")
        return
    
    anorak = artists[0]
    print(f"見つかりました: {anorak['name']} (人気度: {anorak['popularity']})")
    
    # 再帰的関連アーティスト取得
    print("\n=== 再帰的関連アーティスト取得中 ===")
    all_related = await client.dig_related_artists([anorak], depth_limit=2)
    print(f"総取得数: {len(all_related)}")
    
    if not all_related:
        print("関連アーティストが取得できませんでした")
        return
    
    # 条件フィルタリング
    print(f"\n=== 条件フィルタリング ===")
    filtered_artists = []
    
    for artist in all_related:
        popularity = artist.get('popularity', 0)
        genres = [g.lower() for g in artist.get('genres', [])]
        
        print(f"チェック中: {artist['name']} (人気度: {popularity}, ジャンル: {artist.get('genres', [])})")
        
        # 人気度条件（2-50に緩和）
        if 2 <= popularity <= 50:
            # ジャンル条件
            has_japanese_indie = "japanese indie" in genres
            has_math_rock = "math rock" in genres
            has_midwest_emo = "midwest emo" in genres
            has_post_rock = "post rock" in genres
            has_indie_rock = "indie rock" in genres
            has_j_rock = "j-rock" in genres
            
            if has_japanese_indie or has_math_rock or has_midwest_emo or has_post_rock or has_indie_rock or has_j_rock:
                genre_match = []
                if has_japanese_indie: genre_match.append("japanese indie")
                if has_math_rock: genre_match.append("math rock")
                if has_midwest_emo: genre_match.append("midwest emo")
                if has_post_rock: genre_match.append("post rock")
                if has_indie_rock: genre_match.append("indie rock")
                if has_j_rock: genre_match.append("j-rock")
                
                artist['genre_match'] = ', '.join(genre_match)
                filtered_artists.append(artist)
                print(f"  ✓ 条件合致: {artist['name']} (ジャンル: {genre_match})")
    
    print(f"\n条件合致アーティスト: {len(filtered_artists)}")
    
    if filtered_artists:
        # CSV出力
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"anorak_recursive_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'name', 'popularity', 'genres', 'followers', 'parent_id', 'parent_name', 'depth', 'genre_match']
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
                    'depth': artist.get('depth', 1),
                    'genre_match': artist['genre_match']
                })
        
        print(f"CSV出力完了: {csv_file}")
        
        # Supabaseに登録
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
                    'discovery_method': 'recursive_related'
                }).execute()
                print(f"✓ {artist['name']} 登録完了")
            except Exception as e:
                print(f"✗ {artist['name']} 登録エラー: {e}")
    
    print(f"\n=== 完了 ===")
    print(f"総取得数: {len(all_related)}")
    print(f"条件合致数: {len(filtered_artists)}")

if __name__ == "__main__":
    asyncio.run(test_anorak_recursive())