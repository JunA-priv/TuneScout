import asyncio
from apps.etl.sources.spotify import SpotifyClient
from packages.common.settings import settings

async def debug_popularity():
    """人気度フィルタリングをデバッグ"""
    client = SpotifyClient()
    await client.get_access_token()
    
    print(f"設定された人気度範囲: {settings.reco_min_popularity} - {settings.reco_max_popularity}")
    
    # インディーアルバムを取得してアーティストの人気度をチェック
    indie_albums = await client.search_japanese_artists_by_genre("indie", limit=10)
    print(f"\n取得したインディーアルバム: {len(indie_albums)}件")
    
    for i, album in enumerate(indie_albums[:5]):  # 最初の5件をチェック
        for artist in album["artists"]:
            artist_info = await client.get_artist_info(artist["id"])
            popularity = artist_info.get("popularity", 0)
            in_range = settings.reco_min_popularity <= popularity <= settings.reco_max_popularity
            
            print(f"{i+1}. {artist['name']} - 人気度: {popularity} {'✓' if in_range else '✗'}")
            print(f"   ジャンル: {artist_info.get('genres', [])}")
    
    # 新譜からも確認
    print(f"\n新譜からの確認:")
    new_releases = await client.search_new_releases(limit=5)
    for i, album in enumerate(new_releases):
        for artist in album["artists"]:
            artist_info = await client.get_artist_info(artist["id"])
            popularity = artist_info.get("popularity", 0)
            in_range = settings.reco_min_popularity <= popularity <= settings.reco_max_popularity
            
            print(f"{i+1}. {artist['name']} - 人気度: {popularity} {'✓' if in_range else '✗'}")

if __name__ == "__main__":
    asyncio.run(debug_popularity())