import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import datasets, migrations

app = FastAPI(
    title="ERP Migration Accelerator",
    description="Demonstrates AI-accelerated ERP consolidation for Army logistics systems",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(migrations.router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "devin_configured": bool(os.environ.get("DEVIN_API_KEY")),
        "repo_url": os.environ.get(
            "MIGRATION_REPO_URL",
            "https://github.com/heintztyler/erp-migration-accelerator",
        ),
    }


# Serve frontend static files in production
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
