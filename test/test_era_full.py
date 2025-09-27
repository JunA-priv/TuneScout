import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from sqlalchemy.orm import sessionmaker
from packages.common.db import engine, Artist, Base
from packages.common.settings import settings
from scrapers.era_scraper import EraScraper

def search_spotify_artist(sp, artist_name):
    try:
        results = sp.search(q=f'artist:{artist_name}', type='artist', market='JP', limit=1)
        if results['artists']['items']:
            artist = results['artists']['items'][0]
            return {
                'spotify_id': artist['id'],
                'name': artist['name'],
                'popularity': artist['popularity'],
                'followers': artist['followers']['total'],
                'genres': artist['genres'],
                'external_urls': artist['external_urls']
            }
    except Exception as e:
        print(f"Spotify検索エラー ({artist_name}): {e}")
    return None

def save_artist_to_db(session, artist_data):
    existing = session.query(Artist).filter_by(spotify_id=artist_data['spotify_id']).first()
    if existing:
        return False
    
    artist = Artist(
        name=artist_data['name'],
        spotify_id=artist_data['spotify_id'],
        popularity=artist_data['popularity'],
        followers=artist_data['followers'],
        genres=artist_data['genres'],
        external_urls=artist_data['external_urls']
    )
    session.add(artist)
    session.commit()
    return True

def main():
    # Spotify API初期化
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret
    ))
    
    # DB初期化
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        scraper = EraScraper()
        artist_names = scraper.scrape_artists()
        print(f"[{scraper.venue_name}] 取得したアーティスト名: {len(artist_names)}件")
        
        registered_count = 0
        for name in artist_names:
            artist_data = search_spotify_artist(sp, name)
            if not artist_data:
                continue
            
            if 6 <= artist_data['popularity'] <= 24:
                if save_artist_to_db(session, artist_data):
                    print(f"登録: {artist_data['name']} (人気度: {artist_data['popularity']})")
                    registered_count += 1
        
        print(f"[{scraper.venue_name}] 新規登録: {registered_count}件")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()