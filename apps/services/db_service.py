from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update
from packages.common.db import get_supabase_client

class ArtistDBService:
    def __init__(self, session: AsyncSession = None):
        self.session = session
        self.supabase = get_supabase_client()

    async def upsert_artist(self, spotify_data: Dict[str, Any], source: str = "unknown") -> Dict[str, Any]:
        """Spotify APIデータからアーティストを登録/更新"""
        artist_data = self._map_spotify_to_artist(spotify_data)
        
        # 既存チェック
        existing = self.supabase.table("artists").select("*").eq("spotify_id", spotify_data["id"]).execute()
        
        if existing.data:
            # 更新
            result = self.supabase.table("artists").update(artist_data).eq("spotify_id", spotify_data["id"]).execute()
            return result.data[0]
        else:
            # 新規作成
            result = self.supabase.table("artists").insert(artist_data).execute()
            return result.data[0]

    async def upsert_release(self, spotify_data: Dict[str, Any], artist_id: str) -> Dict[str, Any]:
        """リリース情報を登録/更新"""
        release_data = self._map_spotify_to_release(spotify_data, artist_id)
        
        existing = self.supabase.table("releases").select("*").eq("spotify_id", spotify_data["id"]).execute()
        
        if existing.data:
            result = self.supabase.table("releases").update(release_data).eq("spotify_id", spotify_data["id"]).execute()
            return result.data[0]
        else:
            result = self.supabase.table("releases").insert(release_data).execute()
            return result.data[0]

    async def upsert_track(self, spotify_data: Dict[str, Any], release_id: str, artist_id: str) -> Dict[str, Any]:
        """トラック情報を登録/更新"""
        track_data = self._map_spotify_to_track(spotify_data, release_id, artist_id)
        
        existing = self.supabase.table("tracks").select("*").eq("spotify_id", spotify_data["id"]).execute()
        
        if existing.data:
            result = self.supabase.table("tracks").update(track_data).eq("spotify_id", spotify_data["id"]).execute()
            return result.data[0]
        else:
            result = self.supabase.table("tracks").insert(track_data).execute()
            return result.data[0]

    async def get_artist_by_spotify_id(self, spotify_id: str) -> Optional[Dict[str, Any]]:
        """Spotify IDでアーティストを取得"""
        result = self.supabase.table("artists").select("*").eq("spotify_id", spotify_id).execute()
        return result.data[0] if result.data else None

    def _map_spotify_to_artist(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Spotify APIデータをArtistテーブルにマッピング"""
        return {
            "spotify_id": data["id"],
            "name": data["name"],
            "genres": data.get("genres", []),
            "followers": data.get("followers", {}).get("total"),
            "popularity": data.get("popularity"),
            "spotify_url": data.get("external_urls", {}).get("spotify"),
            "images": data.get("images"),
            "source_raw": data
        }

    def _map_spotify_to_release(self, data: Dict[str, Any], artist_id: str) -> Dict[str, Any]:
        """Spotify APIデータをReleaseテーブルにマッピング"""
        return {
            "spotify_id": data["id"],
            "artist_id": artist_id,
            "name": data["name"],
            "release_type": data.get("album_type", "unknown"),
            "total_tracks": data.get("total_tracks"),
            "release_date": data.get("release_date"),
            "release_date_precision": data.get("release_date_precision"),
            "spotify_url": data.get("external_urls", {}).get("spotify"),
            "images": data.get("images"),
            "available_markets": data.get("available_markets", []),
            "label_name_raw": data.get("label"),
            "source_raw": data
        }

    def _map_spotify_to_track(self, data: Dict[str, Any], release_id: str, artist_id: str) -> Dict[str, Any]:
        """Spotify APIデータをTrackテーブルにマッピング"""
        return {
            "spotify_id": data["id"],
            "release_id": release_id,
            "artist_id": artist_id,
            "name": data["name"],
            "track_number": data.get("track_number"),
            "disc_number": data.get("disc_number"),
            "duration_ms": data.get("duration_ms"),
            "explicit": data.get("explicit"),
            "isrc": data.get("external_ids", {}).get("isrc"),
            "is_playable": data.get("is_playable"),
            "spotify_url": data.get("external_urls", {}).get("spotify"),
            "available_markets": data.get("available_markets", []),
            "external_ids": data.get("external_ids"),
            "source_raw": data
        }