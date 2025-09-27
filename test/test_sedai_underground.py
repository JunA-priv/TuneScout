#!/usr/bin/env python3
"""underground japanジャンルのせだいバンドテスト"""

import asyncio
import csv
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def test_sedai_underground():
    """underground japanジャンルのせだいを検索"""
    client = SpotifyClient()
    
    # せだい + underground japan で検索
    if not client.access_token:
        await client.get_access_token()
    
    import httpx
    async with httpx.AsyncClient() as http_client:
        # ジャンル指定検索
        response = await http_client.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {client.access_token}"},
            params={"q": "せだい genre:underground", "type": "artist", "limit": 10}
        )
        
        if response.status_code == 200:
            data = response.json()
            artists = data.get("artists", {}).get("items", [])
            print(f"underground検索結果: {len(artists)}件")
            
            for artist in artists:
                print(f"- {artist['name']} (人気度: {artist['popularity']}, ジャンル: {artist.get('genres', [])})")
        
        # 通常検索でせだいを探す
        response = await http_client.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {client.access_token}"},
            params={"q": "せだい", "type": "artist", "limit": 20}
        )
        
        if response.status_code == 200:
            data = response.json()
            artists = data.get("artists", {}).get("items", [])
            print(f"\n通常検索結果: {len(artists)}件")
            
            # underground japanジャンルを持つアーティストを探す
            target_artist = None
            for artist in artists:
                genres = [g.lower() for g in artist.get('genres', [])]
                if 'underground japan' in genres or any('underground' in g for g in genres):
                    target_artist = artist
                    print(f"✓ 発見: {artist['name']} (人気度: {artist['popularity']}, ジャンル: {artist.get('genres', [])})")
                    break
            
            if not target_artist:
                # ジャンル条件を緩和して最初のせだいを使用
                for artist in artists:
                    if 'せだい' in artist['name'].lower():
                        target_artist = artist
                        print(f"代替選択: {artist['name']} (人気度: {artist['popularity']}, ジャンル: {artist.get('genres', [])})")
                        break
            
            if target_artist:
                print(f"\n=== {target_artist['name']}の関連アーティスト取得 ===")
                all_related = await client.dig_related_artists([target_artist], depth_limit=2)
                print(f"関連アーティスト総数: {len(all_related)}")
                
                # 条件フィルタリング
                filtered_artists = []
                for artist in all_related:
                    popularity = artist.get('popularity', 0)
                    genres = [g.lower() for g in artist.get('genres', [])]
                    
                    if 1 <= popularity <= 40:
                        has_match = any(keyword in ' '.join(genres) for keyword in 
                                      ['japanese indie', 'math rock', 'j-rock', 'underground', 'indie'])
                        
                        if has_match:
                            filtered_artists.append(artist)
                            print(f"✓ {artist['name']} (人気度: {popularity}, ジャンル: {artist.get('genres', [])})")
                
                print(f"\n条件合致アーティスト: {len(filtered_artists)}")
                
                if filtered_artists:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    csv_file = f"sedai_underground_{timestamp}.csv"
                    
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
                    
                    print(f"CSV出力完了: {csv_file}")

if __name__ == "__main__":
    asyncio.run(test_sedai_underground())