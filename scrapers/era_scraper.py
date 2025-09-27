import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base_scraper import BaseScraper

class EraScraper(BaseScraper):
    def __init__(self):
        super().__init__("下北沢ERA", "http://s-era.jp/schedule_cat/")
    
    def get_last_month_url(self):
        """先月の年月を計算してURLを生成"""
        today = datetime.now()
        last_month = today.replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month
        return f"{self.base_url}{year}-{month:02d}"
    
    def scrape_artists(self):
        """下北沢ERAのスケジュールページからアーティスト名を取得"""
        url = self.get_last_month_url()
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        parent_elements = soup.find_all('div', class_='w-flyer')
        
        artist_names = []
        for parent in parent_elements:
            # イベント情報要素を除外
            for detail in parent.find_all('div', class_='detail-texts'):
                detail.decompose()
            for notes in parent.find_all('section', class_='notes-wrapper'):
                notes.decompose()
            
            text = parent.get_text(strip=True)
            if text:
                if '/' in text:
                    names = [name.strip() for name in text.split('/')]
                    artist_names.extend(names)
                else:
                    artist_names.append(text)
        
        return self.filter_artist_names(artist_names)