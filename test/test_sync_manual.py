#!/usr/bin/env python3
"""手動実行用テストスクリプト（過去90日）"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.etl.sources.spotify import SpotifyClient
from apps.etl.pipeline import save_releases_to_db

async def test_sync_90days():
    """過去90日のリリースで同期処理をテスト"""
    print("=== TuneScout 同期処理テスト（過去90日） ===")
    
    try:
        client = SpotifyClient()
        
        # 指定ジャンル
        target_genres = ["rock", "pop", "electronic", "indie", "metal", "alternative"]
        
        all_releases = []
        
        print("\n1. 日本市場の新譜を取得中...")
        new_releases = await client.search_new_releases(market="JP", limit=50)
        print(f"取得した新譜数: {len(new_releases)}")
        
        # 過去90日の範囲を計算
        today = datetime.now()
        ninety_days_ago = today - timedelta(days=90)
        
        print(f"\n2. 過去90日（{ninety_days_ago.strftime('%Y-%m-%d')} 以降）のリリースをフィルタリング中...")
        
        for album in new_releases:
            release_date_str = album.get("release_date", "")
            if not release_date_str:
                continue
                
            # 日付解析
            try:
                if len(release_date_str) == 4:  # 年のみ
                    release_date = datetime.strptime(f"{release_date_str}-01-01", "%Y-%m-%d")
                elif len(release_date_str) == 7:  # 年-月
                    release_date = datetime.strptime(f"{release_date_str}-01", "%Y-%m-%d")
                else:  # 完全な日付
                    release_date = datetime.strptime(release_date_str, "%Y-%m-%d")
                    
                # 過去90日以内かチェック
                if release_date < ninety_days_ago:
                    continue
                    
            except ValueError:
                continue
            
            print(f"  処理中: {album['name']} ({release_date_str})")
            
            # 各アーティストの詳細情報を取得
            for artist in album.get("artists", []):
                try:
                    artist_info = await client.get_artist_info(artist["id"])
                    
                    # 人気度フィルタ（3-24）
                    popularity = artist_info.get("popularity", 100)
                    if not (3 <= popularity <= 24):
                        continue
                        
                    # ジャンルフィルタ
                    artist_genres = [g.lower() for g in artist_info.get("genres", [])]
                    matching_genre = None
                    for genre in target_genres:
                        if genre in " ".join(artist_genres):
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
                    continue
        
        print(f"\n3. 条件に合致したリリース数: {len(all_releases)}")
        
        if all_releases:
            # 結果の詳細表示
            print("\n取得したアーティスト:")
            for i, release_data in enumerate(all_releases[:10]):  # 最初の10件のみ表示
                artist = release_data["artist"]
                album = release_data["release"]
                print(f"{i+1}. {artist['name']} - {album['name']}")
                print(f"   人気度: {artist.get('popularity', 'N/A')}")
                print(f"   ジャンル: {artist.get('genres', [])}")
                print(f"   リリース日: {album.get('release_date', 'N/A')}")
                print()
            
            # データベース保存テスト
            print("4. データベース保存を開始...")
            await save_releases_to_db(all_releases)
            print("データベース保存完了")
        else:
            print("条件に合致するアルバムが見つかりませんでした")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sync_90days())