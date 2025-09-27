import csv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime
import os

# 環境変数からSpotify認証情報を取得
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

def fetch_spotify_data():
    """Spotify APIから新譜データを取得してCSV出力"""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("環境変数SPOTIFY_CLIENT_IDとSPOTIFY_CLIENT_SECRETを設定してください")
        return
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # 新譜を検索
    results = sp.search(q='year:2024', type='album', market='JP', limit=50)
    
    with open(f'spotify_api_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['album_name', 'artist_name', 'release_date', 'total_tracks', 'popularity', 'spotify_id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for album in results['albums']['items']:
            artist = album['artists'][0]
            try:
                artist_info = sp.artist(artist['id'])
                writer.writerow({
                    'album_name': album['name'],
                    'artist_name': artist['name'],
                    'release_date': album['release_date'],
                    'total_tracks': album['total_tracks'],
                    'popularity': artist_info['popularity'],
                    'spotify_id': album['id']
                })
            except Exception as e:
                print(f"エラー: {artist['name']} - {e}")
    
    print(f"Spotify APIデータを出力しました: {len(results['albums']['items'])}件")

if __name__ == "__main__":
    fetch_spotify_data()