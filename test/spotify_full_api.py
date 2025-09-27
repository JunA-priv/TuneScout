"""
Spotify API全フィールド取得モジュール
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
from typing import Dict, List, Optional, Any
import sys
import os
from pathlib import Path
from collections import Counter
import time

# パス設定
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from packages.common.settings import settings


class SpotifyFullAPI:
    def __init__(self):
        self.sp = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=settings.spotify_client_id,
                client_secret=settings.spotify_client_secret
            )
        )

    def get_artist_full(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """アーティストの全フィールドを取得"""
        try:
            return self.sp.artist(artist_id)
        except Exception as e:
            print(f"アーティスト取得エラー: {e}")
            return None

    def get_artist_albums_full(self, artist_id: str, limit: int = 50) -> Optional[Dict[str, Any]]:
        """アーティストのアルバム全フィールドを取得"""
        try:
            # market を付けると地域版の重複が減りやすい
            return self.sp.artist_albums(
                artist_id,
                album_type='album,single,compilation',
                limit=limit,
                country='JP'
            )
        except Exception as e:
            print(f"アルバム取得エラー: {e}")
            return None

    def get_artist_top_tracks_full(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """アーティストの人気楽曲全フィールドを取得"""
        try:
            return self.sp.artist_top_tracks(artist_id, country='JP')
        except Exception as e:
            print(f"人気楽曲取得エラー: {e}")
            return None

    def get_related_artists_full(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """関連アーティスト全フィールドを取得"""
        try:
            result = self.sp.artist_related_artists(artist_id)
            return result
        except Exception as e:
            print(f"関連アーティスト取得エラー (スキップ): {e}")
            return {'artists': []}

    def get_album_full(self, album_id: str) -> Optional[Dict[str, Any]]:
        """アルバム全フィールドを取得（label 取得のため使用）"""
        try:
            return self.sp.album(album_id, market='JP')
        except Exception as e:
            print(f"アルバム詳細取得エラー: {e}")
            return None

    def get_track_full(self, track_id: str) -> Optional[Dict[str, Any]]:
        """楽曲全フィールドを取得"""
        try:
            return self.sp.track(track_id, market='JP')
        except Exception as e:
            print(f"楽曲取得エラー: {e}")
            return None

    def get_audio_features_full(self, track_id: str) -> Optional[Dict[str, Any]]:
        """楽曲のオーディオ特徴量全フィールドを取得"""
        try:
            features = self.sp.audio_features([track_id])
            return features[0] if features and features[0] else None
        except Exception as e:
            print(f"オーディオ特徴量取得エラー (スキップ): {e}")
            return None

    def search_full(self, query: str, search_type: str = 'artist', limit: int = 50) -> Optional[Dict[str, Any]]:
        """検索全フィールドを取得"""
        try:
            return self.sp.search(q=query, type=search_type, limit=limit, market='JP')
        except Exception as e:
            print(f"検索エラー: {e}")
            return None

    # ===== ここから追加: 日本のアーティストかを推定 =====
    JP_LABEL_HINTS = [
        "japan", "jpn", "tokyo", "osaka", "kyoto", "nagoya",
        "sony music japan", "avex", "king records", "victor", "jvc",
        "ponycanyon", "pony canyon", "ki/oon", "p-vine", "p-vine records",
        "space shower", "felicity", "speedstar", "rambling", "virgin music jpn"
    ]

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
        """アルバム詳細を叩いて label を収集（件数が多い場合はAPIレートに注意）"""
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
            # 軽いレート制限回避
            time.sleep(0.15)
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
        """
        日本アーティストかの推定を返す:
        - is_japanese: bool/None
        - confidence: 'high'|'medium'|'low'
        - signals: {genre_has_japanese, isrc_country_counts, label_hits}
        - top_isrc_country: 'JP'等
        - explanation: str
        """
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

        # ISRC (top tracks 由来。必要ならアルバム全曲に拡張可)
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
            is_japanese = None  # どちらとも言えない
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
    # ===== 追加ここまで =====

    def get_complete_artist_data(self, artist_name: str) -> Dict[str, Any]:
        """アーティスト名から全データを取得"""
        result = {
            'artist_name': artist_name,
            'search_result': None,
            'artist_details': None,
            'albums': None,
            'top_tracks': None,
            'related_artists': None,
            'sample_track_features': None,
            # ↓ 追加
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
        top_tracks = self.get_artist_top_tracks_full(artist_id)
        result['top_tracks'] = top_tracks

        # 関連アーティスト
        result['related_artists'] = self.get_related_artists_full(artist_id)

        # サンプル楽曲のオーディオ特徴量
        if top_tracks and top_tracks.get('tracks'):
            sample_track_id = top_tracks['tracks'][0]['id']
            result['sample_track_features'] = self.get_audio_features_full(sample_track_id)

        # ★ 日本アーティスト推定を追加
        result['country_inference'] = self.infer_country_japan(
            result['artist_details'],
            result['top_tracks'],
            result['albums']
        )

        return result


def main():
    """テスト実行"""
    api = SpotifyFullAPI()
    test_artists = ["Anorak", "Tiny Moving Parts", "TTNG", "yard rat"]

    for test_artist in test_artists:
        print(f"\n=== {test_artist} の全データ取得 ===")
        data = api.get_complete_artist_data(test_artist)

        # 結果をJSONファイルに保存
        output_file = f"spotify_full_data_{test_artist.lower().replace(' ', '_')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"データを {output_file} に保存しました")

        # 主要フィールドの表示
        if data['artist_details']:
            artist = data['artist_details']
            print(f"\n=== アーティスト基本情報 ===")
            print(f"名前: {artist.get('name')}")
            print(f"人気度: {artist.get('popularity')}")
            print(f"フォロワー: {(artist.get('followers') or {}).get('total')}")
            print(f"ジャンル: {artist.get('genres')}")
            print(f"Spotify URL: {(artist.get('external_urls') or {}).get('spotify')}")

        # 日本アーティスト推定の表示
        ci = data.get("country_inference")
        if ci:
            print("\n=== 日本アーティスト推定 ===")
            print(f"is_japanese: {ci['is_japanese']} (confidence: {ci['confidence']})")
            print(f"top_isrc_country: {ci['top_isrc_country']}")
            print(f"signals: {ci['signals']}")
            print(f"explanation: {ci['explanation']}")
        
        print("\n" + "="*50)


if __name__ == "__main__":
    main()
