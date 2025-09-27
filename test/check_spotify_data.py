import asyncio
import json
from apps.etl.sources.spotify import SpotifyClient

async def check_spotify_data():
    """Spotify APIから取得したデータを確認"""
    client = SpotifyClient()
    
    print("Spotify APIデータ確認中...")
    
    # 日本のアーティストの新譜を取得
    releases = await client.search_albums_by_country("Japan", limit=10)
    
    print(f"\n新譜データ: {len(releases)}件")
    print("=" * 50)
    
    for i, release in enumerate(releases[:5], 1):
        print(f"\n{i}. アルバム: {release['name']}")
        print(f"   アーティスト: {', '.join([artist['name'] for artist in release['artists']])}")
        print(f"   リリース日: {release['release_date']}")
        print(f"   トラック数: {release['total_tracks']}")
        
        # アーティスト詳細情報を取得
        artist_id = release['artists'][0]['id']
        artist_info = await client.get_artist_info(artist_id)
        print(f"   人気度: {artist_info.get('popularity', 'N/A')}")
        print(f"   フォロワー数: {artist_info.get('followers', {}).get('total', 'N/A'):,}")
        print(f"   ジャンル: {', '.join(artist_info.get('genres', []))}")
    
    # 全データをJSONファイルに保存
    with open('spotify_data_sample.json', 'w', encoding='utf-8') as f:
        json.dump(releases, f, ensure_ascii=False, indent=2)
    
    print(f"\n全データをspotify_data_sample.jsonに保存しました")

if __name__ == "__main__":
    asyncio.run(check_spotify_data())
