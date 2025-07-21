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
    "https://moleai-production.up.railway.app"  # Railway backend
]

# Add production origins from environment variables
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

# For production, allow all Vercel domains (you can make this more specific)
if os.getenv("NODE_ENV") == "production" or os.getenv("ENVIRONMENT") == "production":
    allowed_origins.extend([
        "https://*.vercel.app",
        "https://vercel.app"
    ])

# Allow all HTTPS origins in production (more permissive, you can restrict this)
allow_origin_regex = None
if os.getenv("NODE_ENV") == "production" or os.getenv("ENVIRONMENT") == "production":
    allow_origin_regex = r"https://.*\.vercel\.app"

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