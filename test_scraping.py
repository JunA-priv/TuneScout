#!/usr/bin/env python3
"""スクレイピングテスト"""

from scrapers.era_scraper import EraScraper
from scrapers.jam_scraper import JamScraper

def test_era_scraper():
    print("=== 下北沢ERA スクレイピングテスト ===")
    scraper = EraScraper()
    print(f"URL: {scraper.get_last_month_url()}")
    
    try:
        artists = scraper.scrape_artists()
        print(f"取得アーティスト数: {len(artists)}")
        for i, artist in enumerate(artists[:10], 1):
            print(f"{i:2d}. {artist}")
        if len(artists) > 10:
            print(f"... 他{len(artists) - 10}件")
    except Exception as e:
        print(f"エラー: {e}")

def test_jam_scraper():
    print("\n=== 西永福JAM スクレイピングテスト ===")
    scraper = JamScraper()
    print(f"URL: {scraper.get_last_month_url()}")
    
    try:
        artists = scraper.scrape_artists()
        print(f"取得アーティスト数: {len(artists)}")
        for i, artist in enumerate(artists[:10], 1):
            print(f"{i:2d}. {artist}")
        if len(artists) > 10:
            print(f"... 他{len(artists) - 10}件")
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    test_era_scraper()
    test_jam_scraper()