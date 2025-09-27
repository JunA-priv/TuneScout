"""
スクレイピングアーティストのSpotify処理メイン
"""
import sys
import os
from pathlib import Path

# パス設定
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tunescout.spotify_artist_processor import SpotifyArtistProcessor
from scrapers.ninespice_scraper import NineSpiceScraper
from scrapers.era_scraper import EraScraper
from scrapers.warp_scraper import WarpScraper
from scrapers.jam_scraper import JamScraper
from scrapers.meets_scraper import MeetsScraper
from scrapers.shelter_scraper import ShelterScraper

def main():
    """メイン処理"""
    processor = SpotifyArtistProcessor()
    scrapers = [
        NineSpiceScraper(), 
        EraScraper(), 
        WarpScraper(), 
        JamScraper(), 
        MeetsScraper(), 
        ShelterScraper()
    ]

    total_results = {
        'processed': 0,
        'japanese_found': 0,
        'popularity_filtered': 0,
        'saved_to_supabase': 0,
        'venues': {}
    }

    for scraper in scrapers:
        print(f"\n=== {scraper.venue_name} ===")
        
        # アーティスト名取得
        artist_names = scraper.scrape_artists()
        print(f"取得したアーティスト名: {len(artist_names)}件")
        
        if not artist_names:
            continue

        # Spotify処理
        results = processor.process_scraped_artists(artist_names)
        
        # 結果表示
        print(f"処理済み: {results['processed']}件")
        print(f"日本アーティスト: {results['japanese_found']}件")
        print(f"人気度フィルタ通過: {results['popularity_filtered']}件")
        print(f"Supabase保存: {results['saved_to_supabase']}件 ({results.get('save_status', 'unknown')})")
        
        # 詳細表示
        for artist_data in results['artists_data']:
            print(f"  - {artist_data['name']} (人気度: {artist_data['popularity']}, 信頼度: {artist_data['confidence']})")
        
        # 集計
        total_results['processed'] += results['processed']
        total_results['japanese_found'] += results['japanese_found']
        total_results['popularity_filtered'] += results['popularity_filtered']
        total_results['saved_to_supabase'] += results['saved_to_supabase']
        total_results['venues'][scraper.venue_name] = results

    # 総合結果
    print(f"\n=== 総合結果 ===")
    print(f"全体処理済み: {total_results['processed']}件")
    print(f"全体日本アーティスト: {total_results['japanese_found']}件")
    print(f"全体人気度フィルタ通過: {total_results['popularity_filtered']}件")
    print(f"全体Supabase保存: {total_results['saved_to_supabase']}件")

if __name__ == "__main__":
    main()