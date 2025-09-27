"""
Spotify処理のテストスクリプト
"""
import sys
from pathlib import Path

# パス設定
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tunescout.spotify_artist_processor import SpotifyArtistProcessor

def test_single_artist(artist_name: str):
    """単一アーティストのテスト"""
    processor = SpotifyArtistProcessor()
    
    print(f"=== {artist_name} のテスト ===")
    
    # 全データ取得
    complete_data = processor.get_complete_artist_data(artist_name)
    
    if not complete_data['artist_details']:
        print("アーティストが見つかりませんでした")
        return
    
    artist = complete_data['artist_details']
    country_inference = complete_data['country_inference']
    
    print(f"名前: {artist['name']}")
    print(f"人気度: {artist['popularity']}")
    print(f"フォロワー: {artist['followers']['total']}")
    print(f"ジャンル: {artist['genres']}")
    
    print(f"\n日本アーティスト判定:")
    print(f"  is_japanese: {country_inference['is_japanese']}")
    print(f"  confidence: {country_inference['confidence']}")
    print(f"  explanation: {country_inference['explanation']}")
    
    # 人気度フィルタチェック
    popularity = artist['popularity']
    is_japanese = country_inference.get('is_japanese')
    
    if is_japanese and 6 <= popularity <= 24:
        print(f"\n✅ 条件に合致: 日本アーティスト かつ 人気度 {popularity} (6-24)")
        
        # Supabase形式に変換
        row = processor._to_supabase_artist_row(artist, country_inference)
        print(f"Supabase行データ: {row}")
    else:
        print(f"\n❌ 条件に不適合:")
        if not is_japanese:
            print(f"  - 日本アーティストではない")
        if not (6 <= popularity <= 24):
            print(f"  - 人気度 {popularity} が範囲外 (6-24)")

def main():
    """テスト実行"""
    test_artists = [
        "Anorak",           # 日本のアーティスト例
        "Tiny Moving Parts", # 海外アーティスト例
        "TTNG",             # 海外アーティスト例
        "yard rat"          # 日本のアーティスト例
    ]
    
    for artist in test_artists:
        test_single_artist(artist)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()