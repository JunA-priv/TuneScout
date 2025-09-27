import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base_scraper import BaseScraper

class ShelterScraper(BaseScraper):
    def __init__(self):
        super().__init__("下北沢シェルター", "https://www.loft-prj.co.jp/schedule/shelter/schedule")
    
    def get_last_month_url(self):
        """先月の年月を計算してURLを生成"""
        today = datetime.now()
        last_month = today.replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month
        return f"{self.base_url}?scheduleyear={year}&schedulemonth={month}"
    
    def scrape_artists(self):
        """下北沢シェルターのスケジュールページからアーティスト名を取得"""
        url = self.get_last_month_url()
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        artist_tag_elements = soup.find_all('ul', class_='artist_tag')
        
        artist_names = []
        for ul in artist_tag_elements:
            li_elements = ul.find_all('li')
            for li in li_elements:
                text = li.get_text(strip=True)
                if text:
                    artist_names.append(text)
        
        return self.filter_artist_names(artist_names)