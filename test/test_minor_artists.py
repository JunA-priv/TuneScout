#!/usr/bin/env python3
"""マイナーアーティスト検索テスト"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.etl.sources.spotify import sync_yesterday_releases
from apps.etl.pipeline import save_releases_to_db

async def test_minor_artists():
    """人気度3-24のマイナーアーティストを検索"""
    print("=== マイナーアーティスト検索テスト（過去90日、人気度3-24） ===")
    
    try:
        releases = await sync_yesterday_releases()
        print(f"取得したリリース数: {len(releases)}")
        
        if releases:
            print("\n条件に合致したアーティスト:")
            for i, release_data in enumerate(releases):
                artist = release_data["artist"]
                album = release_data["release"]
                print(f"{i+1}. {artist['name']} - {album['name']}")
                print(f"   人気度: {artist.get('popularity')}")
                print(f"   ジャンル: {artist.get('genres')}")
                print()
            
            await save_releases_to_db(releases)
            print("データベース保存完了")
        else:
            print("条件に合致するマイナーアーティストが見つかりませんでした")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_minor_artists())