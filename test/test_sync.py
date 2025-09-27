#!/usr/bin/env python3
"""動作確認用テストスクリプト"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.etl.sources.spotify import sync_yesterday_releases
from apps.etl.pipeline import save_releases_to_db

async def test_sync():
    """同期処理のテスト実行"""
    print("=== TuneScout 同期処理テスト ===")
    
    try:
        # 1. 昨日リリースの取得テスト
        print("\n1. 昨日リリースの取得を開始...")
        releases = await sync_yesterday_releases()
        print(f"取得したリリース数: {len(releases)}")
        
        if releases:
            # 結果の詳細表示
            print("\n取得したアーティスト:")
            for i, release_data in enumerate(releases[:5]):  # 最初の5件のみ表示
                artist = release_data["artist"]
                album = release_data["release"]
                print(f"{i+1}. {artist['name']} - {album['name']} (人気度: {artist.get('popularity', 'N/A')})")
                print(f"   ジャンル: {artist.get('genres', [])}")
                print(f"   リリース日: {album.get('release_date', 'N/A')}")
                print()
            
            # 2. データベース保存テスト
            print("2. データベース保存を開始...")
            await save_releases_to_db(releases)
            print("データベース保存完了")
        else:
            print("昨日リリースされた条件に合致するアルバムが見つかりませんでした")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sync())