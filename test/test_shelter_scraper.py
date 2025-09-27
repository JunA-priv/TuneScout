from scrapers.shelter_scraper import ShelterScraper

def test_shelter_scraper():
    scraper = ShelterScraper()
    print(f"ライブハウス: {scraper.venue_name}")
    print(f"URL: {scraper.get_last_month_url()}")
    
    artist_names = scraper.scrape_artists()
    print(f"取得したアーティスト名: {len(artist_names)}件")
    
    for name in artist_names[:10]:
        print(f"- {name}")

if __name__ == "__main__":
    test_shelter_scraper()