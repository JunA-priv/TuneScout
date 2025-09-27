from sqlalchemy.orm import sessionmaker
from packages.common.db import engine, Artist

Session = sessionmaker(bind=engine)
session = Session()

artists = session.query(Artist).limit(5).all()
print(f"データベース内のアーティスト数: {session.query(Artist).count()}件")
print("\n登録されたアーティストの詳細情報:")

for artist in artists:
    print(f"\n名前: {artist.name}")
    print(f"人気度: {artist.popularity}")
    print(f"フォロワー数: {artist.followers}")
    print(f"ジャンル: {artist.genres}")
    print(f"外部URL: {artist.external_urls}")

session.close()
