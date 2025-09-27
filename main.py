import os
import sys
import time
import threading
import pathlib
import logging
from typing import Optional, Any, Dict, List, Tuple

import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure local packages can be imported at module load time
_project_root = pathlib.Path(__file__).parent
_src_path = _project_root / "src"
if _src_path.exists():
    _s = str(_src_path)
    if _s not in sys.path:
        sys.path.insert(0, _s)

# Module imports with specific exception handling (top-level only)
try:
    from tunescout.artist_discovery_main import (
        search_spotify_artist,
        _to_supabase_artist_row,
        save_artists_to_supabase,
        main as discovery_main,
    )
except ImportError as e:
    logger.warning(f"Failed to import tunescout modules: {e}")
    search_spotify_artist = None  # type: ignore
    _to_supabase_artist_row = None  # type: ignore
    save_artists_to_supabase = None  # type: ignore
    discovery_main = None  # type: ignore

try:
    from packages.common.gemini import GeminiClient
    from packages.common.db import Base, engine, supabase, supabase_admin
    from packages.common.settings import settings
except ImportError as e:
    logger.warning(f"Failed to import common packages: {e}")
    GeminiClient = None  # type: ignore
    Base = engine = supabase = supabase_admin = settings = None  # type: ignore

try:
    from scrapers.ninespice_scraper import NineSpiceScraper
    from scrapers.era_scraper import EraScraper
    from scrapers.warp_scraper import WarpScraper
    from scrapers.jam_scraper import JamScraper
    from scrapers.meets_scraper import MeetsScraper
    from scrapers.shelter_scraper import ShelterScraper
except ImportError as e:
    logger.warning(f"Failed to import scrapers: {e}")
    NineSpiceScraper = EraScraper = WarpScraper = JamScraper = MeetsScraper = ShelterScraper = None  # type: ignore

try:
    from apps.etl.scheduler import start_scheduler
except ImportError as e:
    logger.warning(f"Failed to import scheduler: {e}")
    start_scheduler = None  # type: ignore

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except ImportError as e:
    logger.warning(f"Failed to import spotipy: {e}")
    spotipy = None  # type: ignore
    SpotifyClientCredentials = None  # type: ignore


def _ensure_src_on_path() -> None:
    """プロジェクトの `src/` を import パスに追加（`tunescout` パッケージの読み込みを保証）。"""
    project_root = pathlib.Path(__file__).parent
    src_path = project_root / "src"
    if src_path.exists():
        s = str(src_path)
        if s not in sys.path:
            sys.path.insert(0, s)


def _start_scheduler_background() -> Optional[threading.Thread]:
    """ETL スケジューラーをデーモンスレッドで起動（有効化されている場合）。"""
    enable = os.getenv("ENABLE_SCHEDULER", "1").lower() not in {"0", "false", "no"}
    if not enable:
        return None

    if start_scheduler is None:  # type: ignore
        logger.error("Failed to start scheduler: start_scheduler not available")
        return None

    t = threading.Thread(target=start_scheduler, name="etl-scheduler", daemon=True)  # type: ignore[arg-type]
    t.start()
    logger.info("ETL scheduler started successfully")
    return t


def _run_discovery_once_background() -> Optional[threading.Thread]:
    """アーティスト探索メインフローを起動時に一度だけバックグラウンドで実行（任意）。

    環境変数 RUN_DISCOVERY_ON_START が真値の場合に有効化。
    """
    enable = os.getenv("RUN_DISCOVERY_ON_START", "").strip()
    if not enable:
        return None

    # `tunescout` はモジュール先頭で import されるため、ここでは実行のみ

    def _target():
        try:
            if discovery_main is None:  # type: ignore
                raise ImportError("discovery_main not available")
            discovery_main()  # type: ignore[operator]
        except ImportError as e:
            logger.error(f"Failed to import discovery main: {e}")
        except Exception as e:
            logger.error(f"Discovery error: {e}")

    t = threading.Thread(target=_target, name="artist-discovery", daemon=True)
    t.start()
    logger.info("Artist discovery background thread started")
    return t


def _truthy_env(name: str, default: str = "") -> bool:
    v = os.getenv(name, default).strip().lower()
    return v in {"1", "true", "yes", "on"}


def _to_profile_row(artist: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Gemini応答を Supabase artist_profiles 行へマッピング"""
    return {
        "artist_id": artist.get("spotify_id"),
        "name": profile.get("name") or artist.get("name"),
        "history": profile.get("history") or profile.get("summary"),
        "base": profile.get("base") or profile.get("origin"),
        "youtube": profile.get("youtube", []),
        "style": profile.get("style") or profile.get("genres"),
        "sources": profile.get("sources", []),
        "last_updated": profile.get("last_updated"),
        "raw": profile,
    }


def _upsert_profiles(rows: List[Dict[str, Any]], chunk: int = 200) -> int:
    """artist_profiles へ upsert（Supabase Admin があればそちらを優先）。"""
    client = supabase_admin or supabase
    if not client:
        logger.warning("Supabase client not configured, skipping profile save")
        return 0

    total = 0
    for i in range(0, len(rows), chunk):
        part = rows[i : i + chunk]
        if not part:
            continue
        try:
            client.table("artist_profiles").upsert(part, on_conflict="artist_id").execute()
            total += len(part)
        except Exception as e:
            logger.error(f"Failed to upsert profiles batch {i//chunk + 1}: {e}")
    return total


def _load_modules() -> Tuple[bool, Dict[str, Any]]:
    """Confirm required modules are available and return them in a dict."""
    modules: Dict[str, Any] = {}

    # tunescout core functions
    if not (search_spotify_artist and _to_supabase_artist_row and save_artists_to_supabase):  # type: ignore
        logger.error("tunescout modules are not available")
        return False, {}
    modules.update({
        'search_spotify_artist': search_spotify_artist,
        '_to_supabase_artist_row': _to_supabase_artist_row,
        'save_artists_to_supabase': save_artists_to_supabase,
    })

    # scrapers
    if not all([NineSpiceScraper, EraScraper, WarpScraper, JamScraper, MeetsScraper, ShelterScraper]):  # type: ignore
        logger.error("One or more scrapers are not available")
        return False, {}
    modules['scrapers'] = [
        NineSpiceScraper(),  # type: ignore[operator]
        EraScraper(),        # type: ignore[operator]
        WarpScraper(),       # type: ignore[operator]
        JamScraper(),        # type: ignore[operator]
        MeetsScraper(),      # type: ignore[operator]
        ShelterScraper(),    # type: ignore[operator]
    ]

    # common packages
    if not (GeminiClient and Base and engine and settings):  # type: ignore
        logger.error("Common packages are not available")
        return False, {}
    modules.update({
        'GeminiClient': GeminiClient,
        'Base': Base,
        'engine': engine,
        'settings': settings,
    })

    return True, modules

def _init_spotify_client(modules: Dict[str, Any]):
    """Initialize Spotify client."""
    if spotipy is None or SpotifyClientCredentials is None:  # type: ignore
        raise ImportError("spotipy is not installed or unavailable")

    if not modules['settings'].spotify_client_id or not modules['settings'].spotify_client_secret:
        raise ValueError("Spotify credentials not configured")

    return spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=modules['settings'].spotify_client_id,
            client_secret=modules['settings'].spotify_client_secret,
        )
    )

def _scrape_and_filter_artists(modules: Dict[str, Any], sp) -> Tuple[Dict[str, dict], Dict[str, Dict[str, Any]]]:
    """Scrape artists and filter by popularity."""
    dedup_rows: dict[str, dict] = {}
    artists_for_gemini: dict[str, Dict[str, Any]] = {}
    
    for sc in modules['scrapers']:
        names = sc.scrape_artists()
        logger.info(f"[{sc.venue_name}] 取得したアーティスト名: {len(names)}件")
        for nm in names:
            try:
                data = modules['search_spotify_artist'](sp, nm)
                if not data:
                    continue
                pop = int(data.get("popularity", 0))
                if 6 <= pop <= 24:
                    row = modules['_to_supabase_artist_row'](data)
                    spotify_id = row.get("spotify_id")
                    if spotify_id:
                        dedup_rows[spotify_id] = row
                        artists_for_gemini[spotify_id] = {"spotify_id": spotify_id, "name": row.get("name"), "popularity": pop}
            except Exception as e:
                logger.warning(f"Error processing artist {nm}: {e}")
    
    return dedup_rows, artists_for_gemini

def _process_gemini_profiles(modules: Dict[str, Any], artists_for_gemini: Dict[str, Dict[str, Any]]) -> None:
    """Process artists through Gemini and save profiles."""
    client = modules['GeminiClient']()
    sleep_sec = max(0.1, float(os.getenv("GEMINI_SLEEP_SEC", "1.0")))
    limit = int(os.getenv("GEMINI_LIMIT", "0") or 0)

    items = list(artists_for_gemini.values())
    if limit > 0:
        items = items[:limit]

    profile_rows: List[Dict[str, Any]] = []
    for idx, ar in enumerate(items, 1):
        name = ar.get("name")
        if not name:
            continue
        logger.info(f"Processing artist {idx}/{len(items)}: {name}")
        try:
            prof = client.research_artist_jp(str(name))
            profile_rows.append(_to_profile_row(ar, prof))
        except Exception as e:
            logger.warning(f"Gemini error for {name}: {e}")
            continue
        if sleep_sec > 0:
            time.sleep(sleep_sec)

    if profile_rows:
        chunk_size = max(1, int(os.getenv("PROFILES_UPSERT_CHUNK", "200")))
        saved = _upsert_profiles(profile_rows, chunk=chunk_size)
        logger.info(f"Saved {saved} profiles")
    else:
        logger.info("No profiles to save")

def run_full_discovery_pipeline() -> None:
    """ライブハウスのスクレイピング→Supabase(artists)→Gemini→Supabase(artist_profiles)。"""
    _ensure_src_on_path()
    
    success, modules = _load_modules()
    if not success:
        logger.error("Failed to load required modules")
        return

    try:
        sp = _init_spotify_client(modules)
    except Exception as e:
        logger.error(f"Failed to initialize Spotify client: {e}")
        return

    try:
        modules['Base'].metadata.create_all(bind=modules['engine'])
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    dedup_rows, artists_for_gemini = _scrape_and_filter_artists(modules, sp)

    if dedup_rows:
        upserted, status = modules['save_artists_to_supabase'](list(dedup_rows.values()))
        logger.info(f"Artists saved - status: {status}, count: {upserted}")
    else:
        logger.info("No artists to save")

    if not artists_for_gemini:
        logger.info("No artists for Gemini processing")
        return

    try:
        _process_gemini_profiles(modules, artists_for_gemini)
    except Exception as e:
        logger.error(f"Gemini processing failed: {e}")


def main():
    # 先に import パスを整えてバックグラウンド処理を開始
    _ensure_src_on_path()

    # フルパイプラインを起動時に同期実行するモード
    # 例: RUN_FULL_DISCOVERY=1 python main.py
    if _truthy_env("RUN_FULL_DISCOVERY"):
        run_full_discovery_pipeline()
        return

    _start_scheduler_background()
    _run_discovery_once_background()

    # FastAPI UI を起動（apps.api.main:app）
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_flag = os.getenv("RELOAD", "").lower() in {"1", "true", "yes"}

    # 注意: reload を有効にするとプロセスが再生成され、上記スレッドは引き継がれません。
    # 本番運用では RELOAD=0 を推奨します。
    uvicorn.run(
        "apps.api.main:app",
        host=host,
        port=port,
        reload=reload_flag,
        factory=False,
    )


if __name__ == "__main__":
    main()
