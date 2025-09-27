from typing import Dict, Any, List, Optional
from .db_service import ArtistDBService
from packages.common.gemini import get_gemini_client
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

class ArtistService:
    def __init__(self):
        self.db_service = ArtistDBService()
        self.gemini = get_gemini_client()
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
        ))

    async def register_from_scraping(self, spotify_ids: List[str]) -> List[Dict[str, Any]]:
        """スクレイピングで取得したSpotify IDsからアーティストを一括登録"""
        results = []
        
        for spotify_id in spotify_ids:
            try:
                # Spotify APIからデータ取得
                artist_data = self.spotify.artist(spotify_id)
                
                # DB登録
                artist = await self.db_service.upsert_artist(artist_data, source="scraping")
                
                # Geminiで詳細情報取得・更新
                enriched = await self.enrich_with_gemini(artist["id"])
                
                results.append(enriched)
            except Exception as e:
                print(f"Error processing {spotify_id}: {e}")
                continue
                
        return results

    async def register_manual(self, spotify_id: str) -> Dict[str, Any]:
        """手動登録: Gemini検索 → 登録ボタン → Supabase登録"""
        # Spotify APIからデータ取得
        artist_data = self.spotify.artist(spotify_id)
        
        # DB登録
        artist = await self.db_service.upsert_artist(artist_data, source="manual")
        
        # Geminiで詳細情報取得・更新
        enriched = await self.enrich_with_gemini(artist["id"])
        
        return enriched

    async def search_with_gemini(self, query: str) -> List[Dict[str, Any]]:
        """Gemini APIでアーティスト検索"""
        prompt = f"""
        アーティスト名「{query}」について、以下の情報を調査してください：
        1. 正式なアーティスト名
        2. ジャンル
        3. 活動期間
        4. 所属レーベル
        5. 代表曲
        6. Spotify ID（可能であれば）
        
        JSON形式で回答してください。
        """
        
        response = self.gemini.generate_content(prompt)
        # レスポンス解析とSpotify検索を組み合わせ
        return await self._parse_gemini_response(response.text)

    async def enrich_with_gemini(self, artist_id: str) -> Dict[str, Any]:
        """Gemini APIでアーティスト詳細情報を取得・更新"""
        artist = await self.db_service.get_artist_by_spotify_id(artist_id)
        if not artist:
            return None
            
        prompt = f"""
        アーティスト「{artist['name']}」について詳細情報を調査してください：
        1. 出身地・国籍
        2. 結成年・活動開始年
        3. メンバー構成
        4. 音楽的影響
        5. 日本での活動歴
        
        JSON形式で回答してください。
        """
        
        response = self.gemini.generate_content(prompt)
        # 詳細情報をDBに保存（別テーブルまたはJSONBフィールド）
        
        return artist

    async def _parse_gemini_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Geminiレスポンスを解析してSpotify検索"""
        # JSONパース + Spotify検索ロジック
        return []