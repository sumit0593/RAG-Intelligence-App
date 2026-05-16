from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import auth_routes, chat_routes, admin_routes
from backend.database.config import engine, Base
import logging

logger = logging.getLogger(__name__)

# Attempt to create DB tables — gracefully skip if DB is unavailable on startup
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created.")
except Exception as e:
    logger.warning(f"Could not connect to database on startup: {e}. Will retry on first request.")

app = FastAPI(title="Enterprise RAG Intelligence System API", description="Production-grade API for RAG with strict RBAC.")

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, tags=["Authentication"])
app.include_router(chat_routes.router, prefix="/api/chat", tags=["Chat & RAG Workflow"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["Administration"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Enterprise RAG API is running"}
