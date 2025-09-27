#!/usr/bin/env python3
"""アルバム人気度デバッグ"""

import asyncio
import sys
import os
import httpx

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.etl.sources.spotify import SpotifyClient

async def debug_album_popularity():
    """アルバム人気度をデバッグ"""
    client = SpotifyClient()
    await client.get_access_token()
    
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {client.access_token}"},
            params={"q": "genre:indie", "type": "album", "market": "JP", "limit": 10}
        )
        
        albums = response.json().get("albums", {}).get("items", [])
        
        for album in albums:
            album_popularity = album.get("popularity", 0)
            print(f"アルバム: {album['name']} (人気度: {album_popularity})")
            
            if 0 <= album_popularity <= 24:
                print("  ✓ アルバム人気度OK")
                
                for artist in album.get("artists", [])[:1]:
                    try:
                        artist_info = await client.get_artist_info(artist["id"])
                        artist_popularity = artist_info.get("popularity", 0)
                        print(f"  アーティスト: {artist_info['name']} (人気度: {artist_popularity})")
                        
                        if 3 <= artist_popularity <= 24:
                            print("    ✓ 両方の条件合致！")
                        else:
                            print("    ✗ アーティスト人気度範囲外")
                    except Exception as e:
                        print(f"    エラー: {e}")
            else:
                print("  ✗ アルバム人気度範囲外")
            print()

if __name__ == "__main__":
    asyncio.run(debug_album_popularity())