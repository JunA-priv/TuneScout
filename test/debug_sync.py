#!/usr/bin/env python3
"""デバッグ用テストスクリプト"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.etl.sources.spotify import SpotifyClient

async def debug_sync():
    """フィルタリング条件をデバッグ"""
    print("=== フィルタリング条件デバッグ ===")
    
    client = SpotifyClient()
    target_genres = ["rock", "pop", "electronic", "indie", "metal", "alternative"]
    
    print("\n1. 日本市場の新譜を取得中...")
    new_releases = await client.search_new_releases(market="JP", limit=10)
    
    for i, album in enumerate(new_releases[:5]):
        print(f"\n--- アルバム {i+1}: {album['name']} ---")
        
        for j, artist in enumerate(album.get("artists", [])):
            print(f"\nアーティスト {j+1}: {artist['name']}")
            
            try:
                artist_info = await client.get_artist_info(artist["id"])
                popularity = artist_info.get("popularity", 0)
                genres = artist_info.get("genres", [])
                
                print(f"  人気度: {popularity}")
                print(f"  ジャンル: {genres}")
                
                # 人気度チェック
                popularity_ok = 3 <= popularity <= 24
                print(f"  人気度OK (3-24): {popularity_ok}")
                
                # ジャンルチェック
                artist_genres_str = " ".join([g.lower() for g in genres])
                genre_matches = []
                for genre in target_genres:
                    if genre in artist_genres_str:
                        genre_matches.append(genre)
                
                print(f"  マッチするジャンル: {genre_matches}")
                print(f"  条件合致: {popularity_ok and len(genre_matches) > 0}")
                
            except Exception as e:
                print(f"  エラー: {e}")

if __name__ == "__main__":
    asyncio.run(debug_sync())