"""
Spotify API全パラメータ取得とアーティスト登録処理
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Dict, List, Optional, Any
from collections import Counter
import time
import sys
import os
from pathlib import Path

# パス設定
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from packages.common.settings import settings
from packages.common.db import supabase, supabase_admin

# 人気度フィルタ定数
MIN_POPULARITY_THRESHOLD = 6
MAX_POPULARITY_THRESHOLD = 24

class SpotifyArtistProcessor:
    def __init__(self):
        self.sp = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret
            )
        )
        
        # 日本のレーベルヒント
        self.JP_LABEL_HINTS = [
            "japan", "jpn", "tokyo", "osaka", "kyoto", "nagoya",
            "sony music japan", "avex", "king records", "victor", "jvc",
            "ponycanyon", "pony canyon", "ki/oon", "p-vine", "p-vine records",
            "space shower", "felicity", "speedstar", "rambling", "virgin music jpn"
        ]

    def get_artist_full(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """アーティストの全フィールドを取得"""
        try:
            return self.sp.artist(artist_id)
        except Exception as e:
            print(f"アーティスト取得エラー: {e}")
            return None

    def get_artist_top_tracks_full(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """アーティストの人気楽曲全フィールドを取得"""
        try:
            return self.sp.artist_top_tracks(artist_id, country='JP')
        except Exception as e:
            print(f"人気楽曲取得エラー: {e}")
            return None

    def get_artist_albums_full(self, artist_id: str, limit: int = 50) -> Optional[Dict[str, Any]]:
        """アーティストのアルバム全フィールドを取得"""
        try:
            return self.sp.artist_albums(
                artist_id,
                album_type='album,single,compilation',
                limit=limit,
                country='JP'
            )
        except Exception as e:
            print(f"アルバム取得エラー: {e}")
            return None

    def get_album_full(self, album_id: str) -> Optional[Dict[str, Any]]:
        """アルバム全フィールドを取得（label 取得のため使用）"""
        try:
            return self.sp.album(album_id, market='JP')
        except Exception as e:
            print(f"アルバム詳細取得エラー: {e}")
            return None

    def search_full(self, query: str, search_type: str = 'artist', limit: int = 50) -> Optional[Dict[str, Any]]:
        """検索全フィールドを取得"""
        try:
            return self.sp.search(q=query, type=search_type, limit=limit, market='JP')
        except Exception as e:
            print(f"検索エラー: {e}")
            return None

    @staticmethod
    def _genre_has_japanese(genres: List[str]) -> bool:
        text = " ".join(genres).lower()
        return "japanese" in text or "japan" in text

    @staticmethod
    def _isrc_country_prefix(isrc: Optional[str]) -> Optional[str]:
        if not isrc or len(isrc) < 2:
            return None
        return isrc[:2].upper()

    def _collect_isrc_countries_from_toptracks(self, top_tracks: Optional[Dict[str, Any]]) -> Counter:
        """top_tracks から ISRC の国コード頻度を集計"""
        counter = Counter()
        if not top_tracks or not top_tracks.get("tracks"):
            return counter
        for t in top_tracks["tracks"]:
            isrc = (t.get("external_ids") or {}).get("isrc")
            cc = self._isrc_country_prefix(isrc)
            if cc:
                counter[cc] += 1
        return counter

    def _collect_labels_from_albums(self, albums_block: Optional[Dict[str, Any]]) -> List[str]:
        """アルバム詳細を叩いて label を収集"""
        labels: List[str] = []
        if not albums_block:
            return labels

        items = albums_block.get("items") or []
        seen: set = set()
        for a in items:
            alb_id = a.get("id")
            if not alb_id or alb_id in seen:
                continue
            seen.add(alb_id)

            alb = self.get_album_full(alb_id)
            if alb and alb.get("label"):
                labels.append(alb["label"])
            time.sleep(0.15)  # レート制限回避
        return labels

    def _labels_have_jp_hint(self, labels: List[str]) -> List[str]:
        """日本由来っぽいラベル名を抽出"""
        hits = []
        for lab in labels:
            low = lab.lower()
            if any(h in low for h in self.JP_LABEL_HINTS):
                hits.append(lab)
        return hits

    def infer_country_japan(self, artist_details: Optional[Dict[str, Any]],
                             top_tracks: Optional[Dict[str, Any]],
                             albums_block: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """日本アーティストかの推定を返す"""
        if not artist_details:
            return {
                "is_japanese": None,
                "confidence": "low",
                "signals": {},
                "top_isrc_country": None,
                "explanation": "アーティスト詳細が取得できないため判定不能"
            }

        genres = artist_details.get("genres", []) or []
        genre_jp = self._genre_has_japanese(genres)

        # ISRC
        isrc_counts = self._collect_isrc_countries_from_toptracks(top_tracks)
        top_isrc_country = isrc_counts.most_common(1)[0][0] if isrc_counts else None

        # Label
        labels = self._collect_labels_from_albums(albums_block)
        label_hits = self._labels_have_jp_hint(labels)

        # ルールベース判定
        score = 0
        reasons = []

        if genre_jp:
            score += 2
            reasons.append("genres に 'japanese' 系タグあり")
        if top_isrc_country == "JP":
            score += 2
            reasons.append("top tracks の ISRC 多数が JP")
        if label_hits:
            score += 1
            reasons.append(f"日本由来のレーベル痕跡: {', '.join(label_hits[:3])}")

        if score >= 4:
            is_japanese = True
            confidence = "high"
        elif score >= 2:
            is_japanese = True
            confidence = "medium"
        elif score == 1:
            is_japanese = None
            confidence = "low"
        else:
            is_japanese = False
            confidence = "low"

        explanation = " / ".join(reasons) if reasons else "根拠が不足しているため推定困難"

        return {
            "is_japanese": is_japanese,
            "confidence": confidence,
            "top_isrc_country": top_isrc_country,
            "signals": {
                "genre_has_japanese": genre_jp,
                "isrc_country_counts": dict(isrc_counts),
                "label_hits": label_hits
            },
            "explanation": explanation
        }

    def get_complete_artist_data(self, artist_name: str) -> Dict[str, Any]:
        """アーティスト名から全データを取得"""
        result = {
            'artist_name': artist_name,
            'search_result': None,
            'artist_details': None,
            'albums': None,
            'top_tracks': None,
            'country_inference': None,
        }

        # 検索
        search_result = self.search_full(f'artist:{artist_name}', 'artist', 1)
        result['search_result'] = search_result

        if not search_result or not search_result['artists']['items']:
            return result

        artist = search_result['artists']['items'][0]
        artist_id = artist['id']

        # アーティスト詳細
        result['artist_details'] = self.get_artist_full(artist_id)

        # アルバム
        result['albums'] = self.get_artist_albums_full(artist_id)

        # 人気楽曲
        result['top_tracks'] = self.get_artist_top_tracks_full(artist_id)

        # 日本アーティスト推定
        result['country_inference'] = self.infer_country_japan(
            result['artist_details'],
            result['top_tracks'],
            result['albums']
        )

        return result

    def _to_supabase_artist_row(self, artist_data: Dict[str, Any], country_inference: Dict[str, Any]) -> Dict[str, Any]:
        """Supabase用のアーティストデータに変換"""
        external = artist_data.get('external_urls') or {}
        return {
            'id': artist_data['id'],
            'name': artist_data['name'],
            'spotify_id': artist_data['id'],
            'country': 'JP' if country_inference.get('is_japanese') else None,
            'popularity': artist_data.get('popularity', 0),
            'followers': artist_data.get('followers', {}).get('total', 0),
            'genres': artist_data.get('genres', []) or [],
            'external_urls': external,
        }

    def save_artists_to_supabase(self, rows: List[Dict[str, Any]]) -> tuple[int, str]:
        """アーティストをSupabaseに保存"""
        if not rows:
            return 0, "no-op"

        client = supabase_admin or supabase
        if not client:
            return 0, "supabase-not-configured"

        try:
            chunk_size = int(os.getenv("SUPABASE_UPSERT_CHUNK", "500"))
        except Exception:
            chunk_size = 500

        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            if not chunk:
                continue
            try:
                client.table('artists').upsert(chunk, on_conflict='id').execute()
                total += len(chunk)
            except Exception as e:
                print(f"Supabase保存エラー: {e}")
                return total, "error"

        return total, "upserted"

    def process_scraped_artists(self, artist_names: List[str]) -> Dict[str, Any]:
        """スクレイピングで取得したアーティストを処理"""
        results = {
            'processed': 0,
            'japanese_found': 0,
            'popularity_filtered': 0,
            'saved_to_supabase': 0,
            'artists_data': []
        }

        supabase_rows = []

        for name in artist_names:
            print(f"処理中: {name}")
            
            # Spotify検索と全データ取得
            complete_data = self.get_complete_artist_data(name)
            results['processed'] += 1

            if not complete_data['artist_details']:
                continue

            artist_details = complete_data['artist_details']
            country_inference = complete_data['country_inference']

            # 日本アーティスト判定
            is_japanese = country_inference.get('is_japanese')
            if is_japanese:
                results['japanese_found'] += 1
                
                # 人気度フィルタ（日本アーティストのみ）
                popularity = artist_details.get('popularity', 0)
                if MIN_POPULARITY_THRESHOLD <= popularity <= MAX_POPULARITY_THRESHOLD:
                    results['popularity_filtered'] += 1
                    
                    # Supabase用データ準備
                    row = self._to_supabase_artist_row(artist_details, country_inference)
                    supabase_rows.append(row)
                    results['artists_data'].append({
                        'name': artist_details['name'],
                        'popularity': popularity,
                        'is_japanese': is_japanese,
                        'confidence': country_inference.get('confidence'),
                        'explanation': country_inference.get('explanation')
                    })

        # Supabaseに保存
        if supabase_rows:
            saved_count, status = self.save_artists_to_supabase(supabase_rows)
            results['saved_to_supabase'] = saved_count
            results['save_status'] = status
        else:
            results['save_status'] = "no-data"

        return results