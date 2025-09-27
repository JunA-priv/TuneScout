import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base_scraper import BaseScraper

class JamScraper(BaseScraper):
    def __init__(self):
        super().__init__("西永福JAM", "https://jam.rinky.info/events")
    
    def get_last_month_url(self):
        """先月の年月を計算してURLを生成"""
        today = datetime.now()
        last_month = today.replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month
        return f"{self.base_url}?date={year}%2F{month:02d}"
    
    def scrape_artists(self):
        """西永福JAMのイベントページからアーティスト名を取得"""
        url = self.get_last_month_url()
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        act_elements = soup.find_all('p', class_='act')
        
        artist_names = []
        for act in act_elements:
            spans = act.find_all('span')
            for span in spans:
                text = span.get_text(strip=True)
                if text:
                    artist_names.append(text)
        
        return self.filter_artist_names(artist_names)