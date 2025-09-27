#!/usr/bin/env python3
"""
シンプルな統合テスト - スクレイピング → Spotify → ローカルDB保存
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
from sqlalchemy.orm import sessionmaker
from packages.common.db import engine, Artist, Base
from packages.common.settings import settings
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

def save_artist_to_local_db(session, artist_data):
    """ローカルDBに保存"""
    existing = session.query(Artist).filter_by(spotify_id=artist_data['spotify_id']).first()
    if existing:
        # 更新
        existing.popularity = artist_data['popularity']
        existing.followers = artist_data['followers']
        existing.genres = artist_data['genres']
        existing.external_urls = artist_data['external_urls']
        session.commit()
        return "updated"
    
    # 新規作成
    artist = Artist(
        name=artist_data['name'],
        spotify_id=artist_data['spotify_id'],
        popularity=artist_data['popularity'],
        followers=artist_data['followers'],
        genres=artist_data['genres'],
        external_urls=artist_data['external_urls']
    )
    session.add(artist)
    session.commit()
    return "created"

def main():
    print("TuneScout シンプル統合テスト")
    print("=" * 40)
    
    # 1. Spotify API初期化
    print("1. Spotify API初期化...")
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret
    ))
    print("✓ Spotify API接続成功")
    
    # 2. ローカルDB初期化
    print("\n2. ローカルDB初期化...")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    print("✓ ローカルDB準備完了")
    
    # 3. スクレイピング
    print("\n3. スクレイピング実行...")
    scraper = NineSpiceScraper()
    artist_names = scraper.scrape_artists()
    print(f"✓ {len(artist_names)}件のアーティスト名を取得")
    
    # 4. Spotify検索 & DB保存
    print("\n4. Spotify検索 & DB保存...")
    created_count = 0
    updated_count = 0
    target_count = 0
    
    # 最初の20件をテスト
    for i, name in enumerate(artist_names[:20]):
        print(f"  処理中 ({i+1}/20): {name}")
        
        # Spotify検索
        artist_data = search_spotify_artist(sp, name)
        if not artist_data:
            print(f"    ✗ Spotify未発見")
            continue
        
        popularity = artist_data['popularity']
        print(f"    ✓ 発見: {artist_data['name']} (人気度: {popularity})")
        
        # 人気度フィルタ
        if 6 <= popularity <= 24:
            target_count += 1
            result = save_artist_to_local_db(session, artist_data)
            if result == "created":
                created_count += 1
                print(f"    ✓ DB新規保存")
            elif result == "updated":
                updated_count += 1
                print(f"    ✓ DB更新")
        else:
            print(f"    - 人気度範囲外 (6-24)")
    
    # 5. 結果表示
    print(f"\n=== 結果 ===")
    print(f"対象アーティスト: {target_count}件")
    print(f"新規保存: {created_count}件")
    print(f"更新: {updated_count}件")
    
    # 6. DB確認
    print(f"\n=== DB確認 ===")
    total_artists = session.query(Artist).count()
    recent_artists = session.query(Artist).order_by(Artist.created_at.desc()).limit(5).all()
    
    print(f"総アーティスト数: {total_artists}件")
    print("最新5件:")
    for artist in recent_artists:
        print(f"  - {artist.name} (人気度: {artist.popularity})")
    
    session.close()
    print("\n✓ テスト完了")

if __name__ == "__main__":
    main()