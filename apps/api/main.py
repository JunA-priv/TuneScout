from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from .routers import auth, recommendations, webhooks
from apps.api.routers import artists
from packages.common.settings import settings

app = FastAPI(title="TuneScout", description="Music Discovery Recommendation System")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# プロジェクトルートからの相対パス
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
template_dir = os.path.join(base_dir, "templates")
static_dir = os.path.join(base_dir, "static")
print(f"Base directory: {base_dir}")
print(f"Template directory: {template_dir}")
print(f"Template directory exists: {os.path.exists(template_dir)}")

templates = Jinja2Templates(directory=template_dir)

# /static をマウント（ロゴ・favicon 等の配信）
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
app.include_router(artists.router, prefix="/artists", tags=["artists"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "supabase_url": settings.supabase_url,
        "supabase_key": settings.supabase_key
    })

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/test-supabase", response_class=HTMLResponse)
async def test_supabase(request: Request):
    return templates.TemplateResponse("test_supabase.html", {
        "request": request,
        "supabase_url": settings.supabase_url,
        "supabase_key": settings.supabase_key
    })
