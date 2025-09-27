from sqlalchemy.orm import sessionmaker
from packages.common.db import engine, Artist

Session = sessionmaker(bind=engine)
session = Session()

artists = session.query(Artist).all()
print(f"データベース内のアーティスト数: {len(artists)}")

for artist in artists[:10]:  # 最初の10件を表示
    print(f"- {artist.name} (人気度: {artist.popularity})")

session.close()
