#!/usr/bin/env python3
"""half sleepが関連アーティストに入る原因調査"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from apps.etl.sources.spotify import SpotifyClient

async def debug_half_sleep():
    """half sleepの関連性を調査"""
    client = SpotifyClient()
    
    # half sleepの情報を取得
    half_sleep_id = "4BOIR1wQyY0XMjVBWqpMiz"
    half_sleep = await client.get_artist_info(half_sleep_id)
    
    print(f"=== {half_sleep['name']} ===")
    print(f"人気度: {half_sleep['popularity']}")
    print(f"ジャンル: {half_sleep.get('genres', [])}")
    print(f"フォロワー: {half_sleep.get('followers', {}).get('total', 0):,}")
    
    # half sleepの関連アーティストを確認
    print(f"\n=== {half_sleep['name']}の関連アーティスト ===")
    half_sleep_related = await client.get_related_artists(half_sleep_id)
    print(f"関連アーティスト数: {len(half_sleep_related)}")
    
    for i, artist in enumerate(half_sleep_related):
        print(f"{i+1}. {artist['name']} (人気度: {artist['popularity']}, ジャンル: {artist.get('genres', [])})")
    
    # 逆方向の調査：これまでテストしたアーティストからhalf sleepへの関連を確認
    test_artists = [
        ("ANORAK!", "1htg5lwXpkH7DwmKnIW9JI"),
        ("yubiori", None),
        ("せだい", None),
        ("weave", "2taISFyrsTRanZU09L0zt2")
    ]
    
    print(f"\n=== 逆方向調査: どのアーティストから{half_sleep['name']}が関連として出現するか ===")
    
    for artist_name, artist_id in test_artists:
        if not artist_id:
            # IDが不明な場合は検索
            artists = await client.search_artists_by_name(artist_name)
            if artists:
                artist_id = artists[0]['id']
            else:
                continue
        
        print(f"\n--- {artist_name} (ID: {artist_id}) ---")
        related_artists = await client.get_related_artists(artist_id)
        
        # half sleepが関連アーティストに含まれているかチェック
        half_sleep_found = False
        for related in related_artists:
            if related['id'] == half_sleep_id:
                half_sleep_found = True
                print(f"✓ {half_sleep['name']}が関連アーティストに含まれています")
                break
        
        if not half_sleep_found:
            print(f"✗ {half_sleep['name']}は関連アーティストに含まれていません")
        
        print(f"関連アーティスト数: {len(related_artists)}")
        for related in related_artists[:3]:  # 上位3件のみ表示
            print(f"  - {related['name']} (人気度: {related['popularity']})")

if __name__ == "__main__":
    asyncio.run(debug_half_sleep())