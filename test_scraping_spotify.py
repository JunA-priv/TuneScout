#!/usr/bin/env python3
"""
スクレイピング & Spotify API 動作確認テスト
"""
import sys
from pathlib import Path

# パス設定
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from packages.common.settings import settings
from scrapers.ninespice_scraper import NineSpiceScraper

def test_spotify_connection():
    """Spotify API接続テスト"""
    print("=== Spotify API接続テスト ===")
    try:
        sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            client_id=settings.spotify_client_id,
            client_secret=settings.spotify_client_secret
        ))
        
        # テスト検索
        results = sp.search(q='artist:Radiohead', type='artist', market='JP', limit=1)
        if results['artists']['items']:
            artist = results['artists']['items'][0]
            print(f"✓ 接続成功: {artist['name']} (人気度: {artist['popularity']})")
            return sp
        else:
            print("✗ 検索結果なし")
            return None
    except Exception as e:
        print(f"✗ Spotify API エラー: {e}")
        return None

def test_scraping():
    """スクレイピングテスト"""
    print("\n=== スクレイピングテスト ===")
    try:
        scraper = NineSpiceScraper()
        artists = scraper.scrape_artists()
        print(f"✓ 9spice スクレイピング成功: {len(artists)}件のアーティスト取得")
        
        # 最初の5件を表示
        for i, artist in enumerate(artists[:5]):
            print(f"  {i+1}. {artist}")
        
        if len(artists) > 5:
            print(f"  ... 他 {len(artists)-5} 件")
        
        return artists
    except Exception as e:
        print(f"✗ スクレイピング エラー: {e}")
        return []

def test_spotify_search(sp, artist_names):
    """Spotify検索テスト"""
    print("\n=== Spotify検索テスト ===")
    if not sp or not artist_names:
        print("✗ Spotify接続またはアーティスト名がありません")
        return
    
    found_count = 0
    target_popularity_count = 0
    
    # 最初の10件をテスト
    test_names = artist_names[:10]
    
    for name in test_names:
        try:
            results = sp.search(q=f'artist:{name}', type='artist', market='JP', limit=1)
            if results['artists']['items']:
                artist = results['artists']['items'][0]
                popularity = artist['popularity']
                found_count += 1
                
                # 人気度フィルタ（6-24）
                if 6 <= popularity <= 24:
                    target_popularity_count += 1
                    print(f"✓ {name} → {artist['name']} (人気度: {popularity}) [対象]")
                else:
                    print(f"  {name} → {artist['name']} (人気度: {popularity}) [範囲外]")
            else:
                print(f"✗ {name} → 見つからず")
        except Exception as e:
            print(f"✗ {name} → エラー: {e}")
    
    print(f"\n結果: {len(test_names)}件中 {found_count}件発見, {target_popularity_count}件が対象範囲")

def main():
    print("TuneScout スクレイピング & Spotify API 動作確認")
    print("=" * 50)
    
    # 1. Spotify API接続テスト
    sp = test_spotify_connection()
    
    # 2. スクレイピングテスト
    artists = test_scraping()
    
    # 3. Spotify検索テスト
    test_spotify_search(sp, artists)
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    main()