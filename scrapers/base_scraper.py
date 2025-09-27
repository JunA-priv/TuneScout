from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """ライブハウススクレイパーの基底クラス"""
    
    def __init__(self, venue_name: str, base_url: str):
        self.venue_name = venue_name
        self.base_url = base_url
    
    @abstractmethod
    def scrape_artists(self) -> list[str]:
        """アーティスト名のリストを取得する抽象メソッド"""
        pass
    
    def filter_artist_names(self, names: list[str]) -> list[str]:
        """共通のフィルタリング処理"""
        filtered = []
        for name in set(names):
            if name and name.strip():
                filtered.append(name.strip())
        return filtered