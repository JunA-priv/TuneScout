import sys
import os
from pathlib import Path

# 直接実行時にトップレベルの `packages/` や `scrapers/` を import できるようにパス追加
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from sqlalchemy.orm import sessionmaker
from packages.common.db import engine, Artist, Base, supabase, supabase_admin
from packages.common.settings import settings
from scrapers.ninespice_scraper import NineSpiceScraper
from scrapers.era_scraper import EraScraper
from scrapers.warp_scraper import WarpScraper
from scrapers.jam_scraper import JamScraper
from scrapers.meets_scraper import MeetsScraper
from scrapers.shelter_scraper import ShelterScraper

def search_spotify_artist(sp, artist_name):
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

def _to_supabase_artist_row(artist_data: dict) -> dict:
    external = artist_data.get('external_urls') or {}
    return {
        'spotify_id': artist_data['spotify_id'],
        'name': artist_data['name'],
        'popularity': artist_data.get('popularity', 0),
        'followers': artist_data.get('followers', 0),
        'genres': artist_data.get('genres', []) or [],
        'spotify_url': external.get('spotify'),
        'source_raw': artist_data,
    }


def save_artists_to_supabase(rows: list[dict]) -> tuple[int, str]:
    # 同一spotify_idの重複を排除（Upsertで同一コマンド内に重複があるとエラーになるため）
    dedup: dict[str, dict] = {}
    for r in rows or []:
        spotify_id = r.get('spotify_id')
        if spotify_id:
            dedup[spotify_id] = r

    payload = list(dedup.values())
    if not payload:
        return 0, "no-op"

    client = supabase_admin or supabase
    if not client:
        return 0, "supabase-not-configured"

    # チャンク分割して送信（大量投入時のエラー回避）
    try:
        chunk_size = int(os.getenv("SUPABASE_UPSERT_CHUNK", "500"))
    except Exception:
        chunk_size = 500

    total = 0
    for i in range(0, len(payload), chunk_size):
        chunk = payload[i : i + chunk_size]
        if not chunk:
            continue
        client.table('artists').upsert(chunk, on_conflict='spotify_id').execute()
        total += len(chunk)

    return total, "upserted"


def save_artist_to_db(session, artist_data):
    existing = session.query(Artist).filter_by(spotify_id=artist_data['spotify_id']).first()
    if existing:
        # 人気度が変動している場合は更新
        if existing.popularity != artist_data['popularity']:
            existing.popularity = artist_data['popularity']
            existing.followers = artist_data['followers']
            existing.genres = artist_data['genres']
            existing.external_urls = artist_data['external_urls']
            session.commit()
            return "updated"
        return False
    
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
    return True

def main():
    # Spotify API初期化
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret
    ))
    
    # DB初期化（Supabase未設定時のフォールバック用）
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        scrapers = [NineSpiceScraper(), EraScraper(), WarpScraper(), JamScraper(), MeetsScraper(), ShelterScraper()]

        # 会場横断でSupabase行を集約（IDで重複排除）
        supabase_dedup: dict[str, dict] = {}
        overall_registered = 0
        overall_updated = 0

        for scraper in scrapers:
            artist_names = scraper.scrape_artists()
            print(f"[{scraper.venue_name}] 取得したアーティスト名: {len(artist_names)}件")

            registered_count = 0
            updated_count = 0
            for name in artist_names:
                # Spotify検索
                artist_data = search_spotify_artist(sp, name)
                if not artist_data:
                    continue

                # 条件チェック（人気度フィルタ）
                if 6 <= artist_data['popularity'] <= 24:
                    row = _to_supabase_artist_row(artist_data)
                    spotify_id = row.get('spotify_id')
                    if spotify_id:
                        supabase_dedup[spotify_id] = row

                    # フォールバック: ローカルDBにも反映
                    result = save_artist_to_db(session, artist_data)
                    if result is True:
                        registered_count += 1
                    elif result == "updated":
                        updated_count += 1

            overall_registered += registered_count
            overall_updated += updated_count
            print(f"[{scraper.venue_name}] ローカルDB: 新規 {registered_count} 件, 更新 {updated_count} 件（Supabaseは全会場集約後にアップサート）")

        # 集約した行を一括アップサート
        rows_all = list(supabase_dedup.values())
        upserted, status = save_artists_to_supabase(rows_all)
        if status == "supabase-not-configured":
            print(f"[ALL] Supabase未設定のためローカルDBのみ反映しました。総新規 {overall_registered} 件, 総更新 {overall_updated} 件")
        else:
            print(f"[ALL] Supabaseへ {upserted} 件アップサート完了（ローカルDB: 総新規 {overall_registered} 件, 総更新 {overall_updated} 件）")

    finally:
        session.close()

if __name__ == "__main__":
    main()
