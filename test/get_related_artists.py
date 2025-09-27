import asyncio
import httpx
from apps.etl.sources.spotify import SpotifyClient

async def main():
    """指定されたアーティストIDから関連アーティストを取得し、人気度2-24でフィルタリング"""
    artist_id = "1htg5lwXpkH7DwmKnIW9JI"
    
    client = SpotifyClient()
    
    try:
        # 元のアーティスト情報を取得
        original_artist = await client.get_artist_info(artist_id)
        print(f"元のアーティスト: {original_artist['name']} (人気度: {original_artist['popularity']})")
        
        # 関連アーティストを取得
        all_related = await client.get_related_artists(artist_id)
        print(f"\n関連アーティスト総数: {len(all_related)}件")
        
        if all_related:
            for artist in all_related:
                print(f"- {artist['name']} (人気度: {artist['popularity']}, ID: {artist['id']})")
                if artist.get('genres'):
                    print(f"  ジャンル: {', '.join(artist['genres'])}")
        else:
            print("関連アーティストが見つかりません。ジャンル検索を試行中...")
            similar_artists = await client.search_similar_artists_by_genre(artist_id)
            print(f"\nジャンル類似アーティスト: {len(similar_artists)}件")
            
            for artist in similar_artists:
                print(f"- {artist['name']} (人気度: {artist['popularity']}, ID: {artist['id']})")
                if artist.get('genres'):
                    print(f"  ジャンル: {', '.join(artist['genres'])}")
                
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"エラー: アーティストID '{artist_id}' が見つかりません")
            print("このIDが正しいかご確認ください")
        else:
            print(f"HTTPエラー: {e.response.status_code} - {e}")
    except Exception as e:
        print(f"予期しないエラー: {e}")

if __name__ == "__main__":
    asyncio.run(main())
