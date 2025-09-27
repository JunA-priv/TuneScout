import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base_scraper import BaseScraper

class WarpScraper(BaseScraper):
    def __init__(self):
        super().__init__("吉祥寺WARP", "http://warp.rinky.info/schedules_cat/")
    
    def get_last_month_url(self):
        """先月の年月を計算してURLを生成"""
        today = datetime.now()
        last_month = today.replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month
        return f"{self.base_url}{year}-{month:02d}"
    
    def scrape_artists(self):
        """吉祥寺WARPのスケジュールページからアーティスト名を取得"""
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
            
            # <br>タグを改行文字に変換
            for br in parent.find_all('br'):
                br.replace_with('\n')
            
            text = parent.get_text()
            if text:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        if '/' in line:
                            names = [name.strip() for name in line.split('/')]
                            artist_names.extend(names)
                        else:
                            artist_names.append(line)
        
        return self.filter_artist_names(artist_names)