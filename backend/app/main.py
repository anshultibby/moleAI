from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import chat
import os

app = FastAPI(
    title="Shopping Deals Chat Agent API",
    description="API for a chat agent that finds shopping deals",
    version="1.0.0"
)

# Configure CORS with specific allowed origins
allowed_origins = [
    "http://localhost:3000", 
    "http://localhost:3005",
    "https://localhost:3000",
    "https://localhost:3005",
    "https://moleai-production.up.railway.app",
    "https://shopmole-ai.vercel.app",
    "https://shopmole-ai-git-main.vercel.app"
]

# Add environment-based frontend URL
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))

# For development and production flexibility
if os.getenv("NODE_ENV") == "production" or os.getenv("ENVIRONMENT") == "production":
    # Allow all HTTPS Vercel domains for this specific app
    allowed_origins.extend([
        "https://shopmole-ai-git-preview.vercel.app",
        "https://shopmole-ai-anshultibby.vercel.app"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://shopmole-ai.*\.vercel\.app",
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
