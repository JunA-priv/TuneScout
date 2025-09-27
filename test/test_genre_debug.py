#!/usr/bin/env python3
"""ジャンルフィルタデバッグ"""

import asyncio
import sys
import os
import httpx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.etl.sources.spotify import SpotifyClient

async def debug_genre_filter():
    """ジャンルフィルタをデバッグ"""
    client = SpotifyClient()
    await client.get_access_token()
    target_genres = ["rock", "pop", "electronic", "indie", "metal", "alternative"]
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {client.access_token}"},
            params={"q": "genre:indie", "type": "album", "market": "JP", "limit": 5}
        )
        
        albums = response.json().get("albums", {}).get("items", [])
        
        for album in albums:
            album_popularity = album.get("popularity", 0)
            if not (0 <= album_popularity <= 24):
                continue
                
            print(f"アルバム: {album['name']}")
            
            for artist in album.get("artists", []):
                try:
                    artist_info = await client.get_artist_info(artist["id"])
                    artist_popularity = artist_info.get("popularity", 0)
                    
                    if not (1 <= artist_popularity <= 24):
                        continue
                    
                    print(f"  アーティスト: {artist_info['name']} (人気度: {artist_popularity})")
                    
                    artist_genres = [g.lower() for g in artist_info.get("genres", [])]
                    print(f"  ジャンル: {artist_genres}")
                    
                    # ジャンルマッチング
                    matching_genre = None
                    for genre in target_genres:
                        if genre in " ".join(artist_genres):
                            matching_genre = genre
                            break
                    
                    print(f"  マッチするジャンル: {matching_genre}")
                    
                    if matching_genre:
                        print("  ✓ 全条件合致！")
                    else:
                        print("  ✗ ジャンル不一致")
                        
                except Exception as e:
                    print(f"  エラー: {e}")
            print()

if __name__ == "__main__":
    asyncio.run(debug_genre_filter())