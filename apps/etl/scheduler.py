import asyncio
import os
import schedule
import time
from datetime import datetime
from typing import List, Dict

from apps.etl.sources.spotify import sync_yesterday_releases
from apps.etl.pipeline import save_releases_to_db
from packages.common.settings import settings

async def daily_artist_sync():
    """毎日実行される前日リリースアーティスト同期タスク"""
    print(f"[{datetime.now()}] 前日リリースアーティストの同期を開始...")
    
    try:
        releases = await sync_yesterday_releases()
        print(f"取得したリリース数: {len(releases)}")
        
        # データベースに保存
        if releases:
            await save_releases_to_db(releases)
        
        print(f"[{datetime.now()}] 同期完了")
        return releases
        
    except Exception as e:
        print(f"[{datetime.now()}] エラーが発生しました: {e}")
        return []

def run_daily_sync():
    """スケジューラーから呼び出される同期関数"""
    asyncio.run(daily_artist_sync())

def start_scheduler():
    """スケジューラーを開始し、定期ジョブを登録"""
    # --- Spotify リリース同期（既存ジョブ） ---
    enable_spotify_sync = os.getenv("ENABLE_SPOTIFY_SYNC", "1").lower() not in {"0", "false", "no"}
    spotify_at = os.getenv("SPOTIFY_SYNC_AT", "09:00")
    if enable_spotify_sync:
        try:
            schedule.every().day.at(spotify_at).do(run_daily_sync)
            print(f"Spotify同期ジョブを登録: 毎日 {spotify_at}")
        except Exception as e:
            print(f"Spotify同期ジョブ登録エラー: {e}")

    # --- スクレイピング実行（新規ジョブ） ---
    enable_scraping = os.getenv("ENABLE_SCRAPING", "1").lower() not in {"0", "false", "no"}
    scrape_every_minutes = os.getenv("SCRAPE_EVERY_MINUTES")
    scrape_at = os.getenv("SCRAPE_AT") or os.getenv("SCHEDULE_SCRAPING_AT") or "03:00"

    if enable_scraping:
        try:
            if scrape_every_minutes:
                interval = int(scrape_every_minutes)
                schedule.every(interval).minutes.do(run_scraping)
                print(f"スクレイピングジョブを登録: {interval}分ごと")
            else:
                schedule.every().day.at(scrape_at).do(run_scraping)
                print(f"スクレイピングジョブを登録: 毎日 {scrape_at}")
        except Exception as e:
            print(f"スクレイピングジョブ登録エラー: {e}")

    print("スケジューラーを開始しました（登録済みジョブを定期実行）")

    while True:
        schedule.run_pending()
        time.sleep(60)  # 1分ごとにチェック

if __name__ == "__main__":
    start_scheduler()

def run_scraping() -> None:
    """スクレイピング処理を実行（各会場のスクレイパー）"""
    print(f"[{datetime.now()}] スクレイピングを開始...")
    try:
        # 遅延インポート：環境によっては src を sys.path へ追加している想定
        from tunescout.artist_discovery_main import main as scrape_main

        scrape_main()
        print(f"[{datetime.now()}] スクレイピング完了")
    except Exception as e:
        print(f"[{datetime.now()}] スクレイピングエラー: {e}")
