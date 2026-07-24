import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.config import settings
from database.init_db import init_db
from api.reports import router as reports_router
from api.admin import router as admin_router
from api.webhook import router as webhook_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentry.app")

app = FastAPI(
    title=f"{settings.APP_NAME} — Multi-Community Intelligence Platform (Powered by Gemma 4)",
    description="Multi-tenant platform architecture supporting KWASU pilot, Malete Town, Ilorin, and beyond."
)

@app.on_event("startup")
def startup_event():
    init_db()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include API Routers
app.include_router(reports_router)
app.include_router(admin_router)
app.include_router(webhook_router)

# Web UI Routes
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/admin", response_class=HTMLResponse)
async def read_admin(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html")

@app.get("/demo", response_class=HTMLResponse)
async def read_demo(request: Request):
    return templates.TemplateResponse(request=request, name="demo.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
