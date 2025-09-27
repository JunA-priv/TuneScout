import csv
from datetime import datetime, timedelta
import random

def generate_mock_artists_csv():
    """モックアーティストデータをCSV出力"""
    mock_artists = [
        {"name": "新人バンドA", "spotify_id": "1a2b3c4d", "country": "JP", "genres": "indie,rock", "popularity": 15, "followers": 1200},
        {"name": "アコースティック太郎", "spotify_id": "2b3c4d5e", "country": "JP", "genres": "acoustic,folk", "popularity": 8, "followers": 850},
        {"name": "エレクトロ姫", "spotify_id": "3c4d5e6f", "country": "JP", "genres": "electronic,pop", "popularity": 22, "followers": 3400},
        {"name": "ジャズ三重奏", "spotify_id": "4d5e6f7g", "country": "JP", "genres": "jazz,instrumental", "popularity": 12, "followers": 950},
        {"name": "シンガーソングライター花子", "spotify_id": "5e6f7g8h", "country": "JP", "genres": "singer-songwriter,pop", "popularity": 18, "followers": 2100},
    ]
    
    filename = f'mock_artists_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['name', 'spotify_id', 'country', 'genres', 'popularity', 'followers', 'created_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for artist in mock_artists:
            artist['created_at'] = datetime.now() - timedelta(days=random.randint(1, 30))
            writer.writerow(artist)
    
    print(f"モックアーティストデータを出力: {filename} ({len(mock_artists)}件)")

def generate_mock_releases_csv():
    """モックリリースデータをCSV出力"""
    mock_releases = [
        {"title": "デビューEP", "spotify_id": "ep1a2b3c", "release_date": "2024-01-15", "total_tracks": 4},
        {"title": "夜明けの歌", "spotify_id": "sg2b3c4d", "release_date": "2024-02-20", "total_tracks": 1},
        {"title": "電子音楽集", "spotify_id": "al3c4d5e", "release_date": "2024-03-10", "total_tracks": 8},
        {"title": "ジャズスタンダード", "spotify_id": "al4d5e6f", "release_date": "2024-01-28", "total_tracks": 6},
        {"title": "心の詩", "spotify_id": "sg5e6f7g", "release_date": "2024-03-05", "total_tracks": 1},
    ]
    
    filename = f'mock_releases_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['title', 'spotify_id', 'release_date', 'total_tracks']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for release in mock_releases:
            writer.writerow(release)
    
    print(f"モックリリースデータを出力: {filename} ({len(mock_releases)}件)")

def generate_spotify_api_mock_csv():
    """Spotify API風のモックデータをCSV出力"""
    mock_spotify_data = [
        {"album_name": "春の新譜", "artist_name": "新人シンガーA", "release_date": "2024-03-15", "total_tracks": 5, "popularity": 12, "spotify_id": "mock1"},
        {"album_name": "インディーロック集", "artist_name": "地下バンドB", "release_date": "2024-03-20", "total_tracks": 7, "popularity": 8, "spotify_id": "mock2"},
        {"album_name": "アコースティックライブ", "artist_name": "弾き語り太郎", "release_date": "2024-03-25", "total_tracks": 6, "popularity": 15, "spotify_id": "mock3"},
        {"album_name": "エレクトロニカ実験", "artist_name": "デジタル音楽家", "release_date": "2024-03-30", "total_tracks": 9, "popularity": 20, "spotify_id": "mock4"},
        {"album_name": "ジャズフュージョン", "artist_name": "モダンジャズ団", "release_date": "2024-04-01", "total_tracks": 8, "popularity": 18, "spotify_id": "mock5"},
    ]
    
    filename = f'mock_spotify_api_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['album_name', 'artist_name', 'release_date', 'total_tracks', 'popularity', 'spotify_id']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for data in mock_spotify_data:
            writer.writerow(data)
    
    print(f"モックSpotify APIデータを出力: {filename} ({len(mock_spotify_data)}件)")

if __name__ == "__main__":
    print("モックデータのCSV出力を開始...")
    
    generate_mock_artists_csv()
    generate_mock_releases_csv()
    generate_spotify_api_mock_csv()
    
    print("CSV出力完了")