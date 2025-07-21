from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import chat
import os

app = FastAPI(
    title="Shopping Deals Chat Agent API",
    description="API for a chat agent that finds shopping deals",
    version="1.0.0"
)

# Configure CORS with environment-based origins
allowed_origins = [
    "http://localhost:3000", 
    "http://localhost:3005",
    "https://localhost:3000",  # For HTTPS localhost
    "https://localhost:3005",   # For HTTPS localhost
    "https://moleai-production.up.railway.app",  # Railway backend
    "https://shopmole-ai.vercel.app"  # Vercel frontend
]

# Add production origins from environment variables
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

# For production, allow all Vercel domains
if os.getenv("NODE_ENV") == "production" or os.getenv("ENVIRONMENT") == "production":
    # Add common Vercel preview domains
    allowed_origins.extend([
        "https://shopmole-ai-git-main.vercel.app",
        "https://shopmole-ai-git-preview.vercel.app"
    ])

# Use regex for Vercel preview deployments
allow_origin_regex = None
if os.getenv("NODE_ENV") == "production" or os.getenv("ENVIRONMENT") == "production":
    allow_origin_regex = r"https://shopmole-ai.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.get("/")
async def root():
    return {"message": "Shopping Deals Chat Agent API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 