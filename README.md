# Shopping Deals Chat Agent

A chat agent that performs deep research to find shopping deals using FastAPI backend and Next.js frontend.

## Quick Start with Docker (Recommended)

The easiest way to run the application is using Docker Compose:

```bash
# Clone the repository and navigate to the project directory
git clone <your-repo-url>
cd moleAI

# Start the application with Docker Compose
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

The application will be available at:
- **Frontend**: http://localhost:3005
- **Backend API**: http://localhost:8005
- **API Documentation**: http://localhost:8005/docs

To stop the application:
```bash
docker-compose down
```

## Project Structure

```
/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── models/
│   │   └── routes/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/         # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   └── components/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Manual Setup (Alternative)

If you prefer to run the services manually without Docker:

### Backend (FastAPI)
1. Navigate to the backend directory: `cd backend`
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (macOS/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Run the server: `uvicorn app.main:app --reload`

### Frontend (Next.js)
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`

## Features

- Real-time chat interface
- AI-powered shopping deal research (placeholder implementation)
- Modern, responsive UI with dark mode support
- RESTful API with automatic documentation
- Dockerized for easy deployment

## Development

- The Docker setup includes volume mounts for hot reloading during development
- Backend runs on port 8005 with auto-reload enabled
- Frontend runs on port 3005 with Next.js development server
- Both services restart automatically if they crash

## Next Steps

- Integrate with actual AI services (OpenAI, Claude, etc.)
- Add real shopping deal APIs (Amazon, eBay, etc.)
- Implement user authentication
- Add database for persistent chat history
- Deploy to production environment 