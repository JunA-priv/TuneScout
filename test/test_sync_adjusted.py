#!/usr/bin/env python3
"""調整済みテストスクリプト"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.etl.sources.spotify import SpotifyClient
from apps.etl.pipeline import save_releases_to_db

async def test_sync_adjusted():
    """調整された条件でテスト"""
    print("=== TuneScout 同期処理テスト（調整版） ===")
    
    client = SpotifyClient()
    target_genres = ["rock", "pop", "electronic", "indie", "metal", "alternative"]
    all_releases = []
    
    print("\n1. 日本市場の新譜を取得中...")
    new_releases = await client.search_new_releases(market="JP", limit=20)
    
    for album in new_releases:
        print(f"  処理中: {album['name']}")
        
        for artist in album.get("artists", []):
            try:
                artist_info = await client.get_artist_info(artist["id"])
                popularity = artist_info.get("popularity", 0)
                genres = artist_info.get("genres", [])
                
                # テスト用に人気度範囲を拡大（0-90）
                if not (0 <= popularity <= 90):
                    continue
                
                # ジャンルチェック
                artist_genres_str = " ".join([g.lower() for g in genres])
                matching_genre = None
                for genre in target_genres:
                    if genre in artist_genres_str:
                        matching_genre = genre
                        break
                
                if matching_genre:
                    all_releases.append({
                        "release": album,
                        "artist": artist_info,
                        "genre": matching_genre
                    })
                    print(f"    ✓ 条件合致: {artist_info['name']} (人気度: {popularity}, ジャンル: {matching_genre})")
                    
            except Exception as e:
                print(f"    エラー: {artist['name']} - {e}")
    
    print(f"\n2. 条件に合致したリリース数: {len(all_releases)}")
    
    if all_releases:
        print("\n取得したアーティスト:")
        for i, release_data in enumerate(all_releases[:5]):
            artist = release_data["artist"]
            album = release_data["release"]
            print(f"{i+1}. {artist['name']} - {album['name']}")
            print(f"   人気度: {artist.get('popularity')}")
            print(f"   ジャンル: {artist.get('genres')}")
            print()
        
        print("3. データベース保存テスト...")
        await save_releases_to_db(all_releases)
        print("保存完了")
    else:
        print("条件に合致するアルバムが見つかりませんでした")

if __name__ == "__main__":
    asyncio.run(test_sync_adjusted())