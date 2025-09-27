from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from apps.services.artist_service import ArtistService

router = APIRouter(prefix="/artists", tags=["artists"])

class ArtistSearchRequest(BaseModel):
    query: str

class ArtistRegisterRequest(BaseModel):
    spotify_id: str

class ScrapingRegisterRequest(BaseModel):
    spotify_ids: List[str]

@router.post("/search")
async def search_artist_with_gemini(request: ArtistSearchRequest) -> List[Dict[str, Any]]:
    """Gemini APIでアーティスト検索"""
    service = ArtistService()
    return await service.search_with_gemini(request.query)

@router.post("/register")
async def register_artist_manual(request: ArtistRegisterRequest) -> Dict[str, Any]:
    """手動登録: 登録ボタン押下時の処理"""
    service = ArtistService()
    return await service.register_manual(request.spotify_id)

@router.post("/scraping/register")
async def register_from_scraping(request: ScrapingRegisterRequest) -> List[Dict[str, Any]]:
    """スクレイピング処理による一括登録"""
    service = ArtistService()
    return await service.register_from_scraping(request.spotify_ids)

@router.get("/{spotify_id}")
async def get_artist(spotify_id: str) -> Dict[str, Any]:
    """アーティスト詳細取得"""
    service = ArtistService()
    artist = await service.db_service.get_artist_by_spotify_id(spotify_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist