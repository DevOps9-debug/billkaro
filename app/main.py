from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import time

from app.database import Base, engine
from app.routers import customers, items, custom_columns, settings, invoices, dashboard, auth


def wait_for_db_and_create_tables(retries: int = 15, delay: int = 2):
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as e:
            print(f"DB not ready (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to database after retries")


wait_for_db_and_create_tables()

app = FastAPI(title="BillKaro API")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
app.include_router(custom_columns.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")

FRONTEND_DIR = "/app/static"

if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        return FileResponse(index_path)
