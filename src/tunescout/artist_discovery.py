import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from sqlalchemy.orm import sessionmaker
from packages.common.db import engine, Artist, Base
from packages.common.settings import settings
import re
from datetime import datetime, timedelta

def scrape_schedule():
    # 先月の年月を計算
    today = datetime.now()
    last_month = today.replace(day=1) - timedelta(days=1)
    year = last_month.year
    month = last_month.month
    
    url = f"https://9spices.rinky.info/schedule/?sch-year={year}&sch-mon={month:02d}"
    response = requests.get(url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    parent_elements = soup.find_all('div', class_='sch-actlist')
    
    artist_names = []
    for parent in parent_elements:
        child_elements = parent.find_all('p', class_='actlist-name-p')
        for child in child_elements:
            text = child.get_text(strip=True)
            # "/"で分割
            if '/' in text:
                names = [name.strip() for name in text.split('/')]
                artist_names.extend(names)
            else:
                artist_names.append(text)
    
    # 重複除去とフィルタリング
    filtered_names = []
    for name in set(artist_names):
        if name and not re.match(r'^(and more|andmore)\.{2,}$', name, re.IGNORECASE):
            filtered_names.append(name)
    
    return filtered_names

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
        # スクレイピング
        artist_names = scrape_schedule()
        print(f"取得したアーティスト名: {len(artist_names)}件")
        
        registered_count = 0
        for name in artist_names:
            # Spotify検索
            artist_data = search_spotify_artist(sp, name)
            if not artist_data:
                continue
            
            # 条件チェック（人気度フィルタ）
            if 6 <= artist_data['popularity'] <= 24:
                if save_artist_to_db(session, artist_data):
                    print(f"登録: {artist_data['name']} (人気度: {artist_data['popularity']})")
                    registered_count += 1
        
        print(f"新規登録: {registered_count}件")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()
