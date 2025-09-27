import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from .base_scraper import BaseScraper

class NineSpiceScraper(BaseScraper):
    def __init__(self):
        super().__init__("9spice", "https://9spices.rinky.info/schedule/")
    
    def get_last_month_url(self):
        """先月の年月を計算してURLを生成"""
        today = datetime.now()
        last_month = today.replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month
        return f"{self.base_url}?sch-year={year}&sch-mon={month:02d}"
    
    def scrape_artists(self):
        """9spiceのスケジュールページからアーティスト名を取得"""
        url = self.get_last_month_url()
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        parent_elements = soup.find_all('div', class_='sch-actlist')
        
        artist_names = []
        for parent in parent_elements:
            child_elements = parent.find_all('p', class_='actlist-name-p')
            for child in child_elements:
                text = child.get_text(strip=True)
                # "/"で分割
                if '/' in text:
                    names = [name.strip() for name in text.split('/')]
                    artist_names.extend(names)
                else:
                    artist_names.append(text)
        
        # 重複除去とフィルタリング
        filtered_names = []
        for name in set(artist_names):
            if name and not re.match(r'^(and more|andmore)\.{2,}$', name, re.IGNORECASE):
                filtered_names.append(name)
        
        return filtered_names