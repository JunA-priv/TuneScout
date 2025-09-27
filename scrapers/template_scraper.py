import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

class TemplateScraper(BaseScraper):
    """他のライブハウス用のテンプレートスクレイパー"""
    
    def __init__(self, venue_name: str, base_url: str):
        super().__init__(venue_name, base_url)
    
    def scrape_artists(self) -> list[str]:
        """
        各ライブハウスに応じてカスタマイズが必要な部分
        
        実装例:
        1. URLを構築
        2. HTMLを取得
        3. BeautifulSoupでパース
        4. アーティスト名を抽出
        5. フィルタリングして返す
        """
        url = self.base_url  # 必要に応じてパラメータを追加
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ここを各ライブハウスのHTML構造に合わせて変更
        artist_elements = soup.find_all('div', class_='artist-name')  # 例
        
        artist_names = []
        for element in artist_elements:
            text = element.get_text(strip=True)
            # 必要に応じて分割処理
            if '/' in text:
                names = [name.strip() for name in text.split('/')]
                artist_names.extend(names)
            else:
                artist_names.append(text)
        
        return self.filter_artist_names(artist_names)