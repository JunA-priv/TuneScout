from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from supabase import create_client, Client

from .settings import settings

# Vector型の条件付きインポート
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

# Supabase client - 有効なURLの場合のみ初期化
supabase: Client = None
supabase_admin: Client = None

if settings.supabase_url and not settings.supabase_url.startswith('your_'):
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_key)
        supabase_admin = create_client(settings.supabase_url, settings.supabase_service_key)
    except Exception as e:
        print(f"Supabase初期化エラー: {e}")
        supabase = None
        supabase_admin = None

def _is_truthy_env(name: str) -> bool:
    v = os.getenv(name, "").strip().lower()
    return v in {"1", "true", "yes", "on"}


def _ensure_sslmode(url: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("sslmode", "require")
    new_qs = urlencode(query)
    return urlunparse(parsed._replace(query=new_qs))


def _build_pooler_url_from_direct(url: str, region: str | None) -> str | None:
    """Supabaseの直結URL(postgres)からPooler(pgBouncer)URLに変換。

    例: postgresql+psycopg://postgres:pw@db.<ref>.supabase.co:5432/postgres
      → postgresql+psycopg://postgres:pw@aws-<region>.pooler.supabase.com:6543/postgres?sslmode=require
    region が不明な場合は None を返す。
    """
    if not region:
        return None
    p = urlparse(url)
    if not p.hostname or ".supabase.co" not in p.hostname:
        return None
    # ホストをプーラーに差し替え、ポートを6543へ
    host = f"aws-{region}.pooler.supabase.com"
    netloc = p.netloc
    # netloc は "user:pass@host:port" 形式。host部分だけ差し替え。
    # 安全のため、urlunparseを使うために各構成要素を再構築
    username = p.username or ""
    password = p.password or ""
    auth = username
    if password:
        auth += f":{password}"
    if auth:
        auth += "@"
    new_netloc = f"{auth}{host}:6543"
    new_url = urlunparse(p._replace(netloc=new_netloc))
    return _ensure_sslmode(new_url)


# SQLAlchemy for direct DB operations
def get_db_url():
    # 1) 優先: プーラーURLが別途指定されている場合
    if getattr(settings, "database_url_pooler", ""):
        pooler_url = _ensure_sslmode(settings.database_url_pooler)
        try:
            test_engine = create_engine(pooler_url)
            test_engine.connect().close()
            return pooler_url
        except Exception as e:
            print(f"Supabase Pooler接続失敗、次の選択肢を試行: {e}")

    # 2) USE_SUPABASE_POOLER=1 かつ直結URLが与えられている場合、プーラーURLを生成して試行
    if settings.database_url and _is_truthy_env("USE_SUPABASE_POOLER"):
        pooler_url = _build_pooler_url_from_direct(settings.database_url, getattr(settings, "supabase_region", "") or None)
        if pooler_url:
            try:
                test_engine = create_engine(pooler_url)
                test_engine.connect().close()
                return pooler_url
            except Exception as e:
                print(f"自動生成したPooler接続失敗、直結/SQLiteへフォールバック: {e}")

    # 3) 従来の database_url を試行
    if settings.database_url and not settings.database_url.startswith('postgresql+psycopg://postgres:your_'):
        try:
            test_engine = create_engine(settings.database_url)
            test_engine.connect().close()
            return settings.database_url
        except Exception as e:
            print(f"PostgreSQL接続失敗、SQLiteを使用: {e}")

    # 4) デフォルトのURL（テスト用）
    return "sqlite:///./test.db"

engine = create_engine(get_db_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Artist(Base):
    __tablename__ = "artists"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    spotify_id = Column(String, unique=True)
    country = Column(String)
    genres = Column(JSON)
    popularity = Column(Integer)
    followers = Column(Integer)
    external_urls = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Release(Base):
    __tablename__ = "releases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist_id = Column(UUID(as_uuid=True), nullable=False)
    spotify_id = Column(String, unique=True)
    title = Column(String, nullable=False)
    release_date = Column(DateTime)
    total_tracks = Column(Integer)
    external_urls = Column(JSON)

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, nullable=False)
    url = Column(String, unique=True)
    title = Column(String, nullable=False)
    lang = Column(String, default="en")
    published_at = Column(DateTime)
    author = Column(String)
    raw_text = Column(Text)

class ArticleEmbedding(Base):
    __tablename__ = "article_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), nullable=False)
    embedding = Column(Vector(settings.vector_dim) if VECTOR_AVAILABLE else Text)
    model = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, nullable=False)
    timezone = Column(String, default="UTC")
    preferences = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_supabase_client() -> Client:
    """Supabaseクライアントを取得"""
    if supabase is None:
        raise RuntimeError("Supabase client not initialized")
    return supabase
