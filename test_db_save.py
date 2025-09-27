#!/usr/bin/env python3
"""
データベース保存機能テスト
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
from packages.common.db import supabase, supabase_admin
from scrapers.ninespice_scraper import NineSpiceScraper

def search_spotify_artist(sp, artist_name):
    """Spotify検索"""
    try:
        results = sp.search(q=f'artist:{artist_name}', type='artist', market='JP', limit=1)
        if results['artists']['items']:
            artist = results['artists']['items'][0]
            return {
                'spotify_id': artist['id'],
                'name': artist['name'],
                'popularity': artist['popularity'],
                'followers': artist['followers']['total'],
                'genres': artist['genres'],
                'external_urls': artist['external_urls']
            }
    except Exception as e:
        print(f"Spotify検索エラー ({artist_name}): {e}")
    return None

def to_supabase_row(artist_data):
    """Supabase用データ変換"""
    external = artist_data.get('external_urls') or {}
    return {
        'id': artist_data['spotify_id'],
        'name': artist_data['name'],
        'popularity': artist_data.get('popularity', 0),
        'followers': artist_data.get('followers', 0),
        'genres': artist_data.get('genres', []) or [],
        'spotify_url': external.get('spotify'),
    }

def test_supabase_connection():
    """Supabase接続テスト"""
    print("=== Supabase接続テスト ===")
    try:
        client = supabase_admin or supabase
        if not client:
            print("✗ Supabase未設定")
            return False
        
        # テーブル存在確認
        result = client.table('artists').select('count').execute()
        print(f"✓ Supabase接続成功: artists テーブル確認")
        return True
    except Exception as e:
        print(f"✗ Supabase接続エラー: {e}")
        return False

def test_data_save():
    """データ保存テスト"""
    print("\n=== データ保存テスト ===")
    
    # Spotify API初期化
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret
    ))
    
    # スクレイピング
    scraper = NineSpiceScraper()
    artist_names = scraper.scrape_artists()[:5]  # 最初の5件のみテスト
    
    saved_artists = []
    
    for name in artist_names:
        # Spotify検索
        artist_data = search_spotify_artist(sp, name)
        if not artist_data:
            continue
        
        # 人気度フィルタ
        if 6 <= artist_data['popularity'] <= 24:
            row = to_supabase_row(artist_data)
            saved_artists.append(row)
            print(f"✓ 保存対象: {artist_data['name']} (人気度: {artist_data['popularity']})")
    
    if not saved_artists:
        print("✗ 保存対象のアーティストなし")
        return
    
    # Supabase保存テスト
    try:
        client = supabase_admin or supabase
        result = client.table('artists').upsert(saved_artists, on_conflict='id').execute()
        print(f"✓ Supabase保存成功: {len(saved_artists)}件")
        
        # 保存確認
        for artist in saved_artists:
            check = client.table('artists').select('*').eq('id', artist['id']).execute()
            if check.data:
                print(f"  確認: {check.data[0]['name']} (ID: {artist['id'][:8]}...)")
    
    except Exception as e:
        print(f"✗ Supabase保存エラー: {e}")

def main():
    print("TuneScout データベース保存テスト")
    print("=" * 40)
    
    # 1. Supabase接続テスト
    if not test_supabase_connection():
        return
    
    # 2. データ保存テスト
    test_data_save()
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    main()