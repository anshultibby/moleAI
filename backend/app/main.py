from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import chat

app = FastAPI(
    title="Shopping Deals Chat Agent API",
    description="API for a chat agent that finds shopping deals",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3005"],  # Added port 3005 for frontend
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