from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""
    supabase_db_password: str = ""
    
    # Database
    database_url: str = ""
    database_url_pooler: str = ""
    supabase_region: str = ""
    supabase_project_ref: str = ""
    supabase_db_user: str = ""
    supabase_db_name: str = ""
    
    redis_url: str = "redis://localhost:6379"
    vector_dim: int = 768
    embedding_model: str = "intfloat/multilingual-e5-base"
    
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    
    mail_provider: str = "sendgrid"
    sendgrid_api_key: str = ""
    
    reco_min_popularity: int = 0
    reco_max_popularity: int = 20
    reco_fresh_days: int = 90

    market: str = "JP"
    limit: int = 50

    # Gemini / Google Generative AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    
    class Config:
        env_file = ".env"
    
settings = Settings()
