import csv
import os
from datetime import datetime
from packages.common.db import SessionLocal, Artist, Release

def export_artists_to_csv():
    """アーティストデータをCSVに出力"""
    db = SessionLocal()
    try:
        artists = db.query(Artist).all()
        
        with open(f'artists_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'name', 'spotify_id', 'country', 'genres', 'popularity', 'followers', 'created_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for artist in artists:
                writer.writerow({
                    'id': str(artist.id),
                    'name': artist.name,
                    'spotify_id': artist.spotify_id,
                    'country': artist.country,
                    'genres': ','.join(artist.genres) if artist.genres else '',
                    'popularity': artist.popularity,
                    'followers': artist.followers,
                    'created_at': artist.created_at
                })
        
        print(f"アーティストデータを出力しました: {len(artists)}件")
    finally:
        db.close()

def export_releases_to_csv():
    """リリースデータをCSVに出力"""
    db = SessionLocal()
    try:
        releases = db.query(Release).all()
        
        with open(f'releases_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'artist_id', 'spotify_id', 'title', 'release_date', 'total_tracks']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for release in releases:
                writer.writerow({
                    'id': str(release.id),
                    'artist_id': str(release.artist_id),
                    'spotify_id': release.spotify_id,
                    'title': release.title,
                    'release_date': release.release_date,
                    'total_tracks': release.total_tracks
                })
        
        print(f"リリースデータを出力しました: {len(releases)}件")
    finally:
        db.close()



if __name__ == "__main__":
    print("データベースからCSV出力を開始...")
    
    # DBからのデータ出力
    export_artists_to_csv()
    export_releases_to_csv()
    
    print("CSV出力完了")