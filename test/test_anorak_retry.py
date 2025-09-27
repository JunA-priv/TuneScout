#!/usr/bin/env python3
"""ANORAK!関連アーティスト再取得テスト"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient
from packages.common.db import supabase

async def test_anorak_retry():
    """ANORAK!の関連アーティストを再取得"""
    client = SpotifyClient()
    
    # ANORAK!を検索
    print("=== ANORAK!を検索中 ===")
    artists = await client.search_artists_by_name("ANORAK!")
    
    if not artists:
        print("ANORAK!が見つかりません")
        return
    
    anorak = artists[0]
    print(f"見つかりました: {anorak['name']}")
    print(f"人気度: {anorak['popularity']}")
    print(f"ジャンル: {anorak.get('genres', [])}")
    print(f"ID: {anorak['id']}")
    
    # 関連アーティスト取得（改良版）
    print("\n=== 関連アーティスト取得中 ===")
    related_artists = await client.get_related_artists(anorak['id'])
    print(f"関連アーティスト数: {len(related_artists)}")
    
    if not related_artists:
        print("関連アーティストが取得できませんでした")
        return
    
    # 全関連アーティストの詳細表示
    all_related = []
    for i, artist in enumerate(related_artists):
        popularity = artist.get('popularity', 0)
        genres = artist.get('genres', [])
        followers = artist.get('followers', {}).get('total', 0)
        
        print(f"\n{i+1}. {artist['name']}")
        print(f"   人気度: {popularity}")
        print(f"   ジャンル: {genres}")
        print(f"   フォロワー: {followers:,}")
        
        # 親情報を追加
        artist['parent_id'] = anorak['id']
        artist['parent_name'] = anorak['name']
        all_related.append(artist)
    
    # 条件フィルタリング（緩和版）
    print(f"\n=== 条件フィルタリング ===")
    filtered_artists = []
    
    for artist in all_related:
        popularity = artist.get('popularity', 0)
        genres = [g.lower() for g in artist.get('genres', [])]
        
        # 人気度条件を緩和（2-40）
        if 2 <= popularity <= 40:
            # ジャンル条件
            has_japanese_indie = "japanese indie" in genres
            has_math_rock = "math rock" in genres
            has_midwest_emo = "midwest emo" in genres
            has_post_rock = "post rock" in genres
            has_indie = "indie" in ' '.join(genres)
            
            if has_japanese_indie or has_math_rock or has_midwest_emo or has_post_rock or has_indie:
                genre_match = []
                if has_japanese_indie: genre_match.append("japanese indie")
                if has_math_rock: genre_match.append("math rock")
                if has_midwest_emo: genre_match.append("midwest emo")
                if has_post_rock: genre_match.append("post rock")
                if has_indie and not genre_match: genre_match.append("indie")
                
                artist['genre_match'] = ', '.join(genre_match)
                filtered_artists.append(artist)
                print(f"✓ {artist['name']} (人気度: {popularity}, ジャンル: {genre_match})")
    
    print(f"\n条件合致アーティスト: {len(filtered_artists)}")
    
    if filtered_artists:
        # CSV出力
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"anorak_related_retry_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
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
                    'discovery_method': 'related_artist'
                }).execute()
                print(f"✓ {artist['name']} 登録完了")
            except Exception as e:
                print(f"✗ {artist['name']} 登録エラー: {e}")
    
    print(f"\n=== 完了 ===")
    print(f"総関連アーティスト数: {len(all_related)}")
    print(f"条件合致数: {len(filtered_artists)}")

if __name__ == "__main__":
    asyncio.run(test_anorak_retry())