from scrapers.jam_scraper import JamScraper
import csv
from datetime import datetime

def test_jam_scraper():
    scraper = JamScraper()
    print(f"ライブハウス: {scraper.venue_name}")
    print(f"URL: {scraper.get_last_month_url()}")
    
    artist_names = scraper.scrape_artists()
    print(f"取得したアーティスト名: {len(artist_names)}件")
    
    # CSV出力
    filename = f"jam_artists_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['artist_name'])
        for name in artist_names:
            writer.writerow([name])
    
    print(f"CSVファイルに出力: {filename}")

if __name__ == "__main__":
    test_jam_scraper()