# MoleAI - Shopping Deals Chat Agent

An AI-powered chat agent that performs deep research to find shopping deals using FastAPI backend and Next.js frontend.

## 🚀 Quick Start with Docker

The recommended way to run the application is using Docker Compose:

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd moleAI

# 2. Set up environment variables
cp backend/env-example backend/.env
cp frontend/env-example frontend/.env.local

# 3. Get API credentials
# Email the project owner for API keys and update backend/.env
# The frontend/.env.local should work with default values for local development

# 4. Start the application
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

The application will be available at:
- **Frontend**: http://localhost:3005
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

To stop the application:
```bash
docker-compose down
```

## 🔧 Manual Setup (Not Recommended)

<details>
<summary>Click to expand manual setup instructions</summary>

### Prerequisites
- Python 3.11+
- Node.js 18+
- API credentials (email project owner)

### 1. Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Copy environment template
cp env-example .env

# Edit .env file with your API credentials
# (Email project owner for credentials)

# Create and activate virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### 2. Frontend Setup (Next.js)

```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Copy environment template
cp env-example .env.local

# Edit .env.local and set NEXT_PUBLIC_API_URL=http://localhost:8000

# Install dependencies
npm install

# Start development server
npm run dev -- --port 3005
```

Frontend will be available at: http://localhost:3005

</details>

## 🔑 API Credentials

This application requires several API keys to function. **Email the project owner for credentials.**

### Required APIs:
- **Gemini AI** - Primary language model
- **Firecrawl** - Web scraping service
- **Exa** - Search service
- **Google Custom Search Engine** - Store discovery

### Optional APIs:
- **Jina AI** - Enhanced web scraping
- **Rye** - Amazon/Walmart/Target integration
- **OpenAI** - Alternative language model
- **ScrapFly** - Alternative scraping service

## 📁 Project Structure

```
moleAI/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Main application
│   │   ├── models/         # Data models
│   │   ├── routes/         # API routes
│   │   └── utils/          # Core services
│   ├── env-example         # Environment template
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app directory
│   │   ├── components/    # React components
│   │   └── types/         # TypeScript types
│   ├── env-example        # Environment template
│   ├── package.json       # Node dependencies
│   └── Dockerfile.dev     # Frontend container
├── docker-compose.yml     # Docker orchestration
└── README.md             # This file
```

## ✨ Features

- **Real-time Chat Interface** - Streaming responses with live updates
- **Multi-Store Product Search** - Searches across Shopify, Amazon, Walmart, Target
- **AI-Powered Research** - Uses advanced LLMs for intelligent product discovery
- **Price Filtering & Comparison** - Filter by price ranges and compare deals
- **Responsive Design** - Works on desktop and mobile devices
- **Dark Mode Support** - Automatic dark/light theme detection

## 🛠️ Development

### Hot Reloading
- Backend: FastAPI auto-reloads on file changes
- Frontend: Next.js hot reloads components and pages
- Docker: Includes volume mounts for development

### Testing
```bash
# Backend tests (run in backend directory)
cd backend
python test_*.py

# Frontend linting
cd frontend
npm run lint
```

### Viewing Logs
```bash
# View logs for all services
docker-compose logs

# View logs for specific service
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

## 🚢 Deployment

### Environment Variables for Production

**Backend (.env):**
```bash
NODE_ENV=production
ENVIRONMENT=production
FRONTEND_URL=https://your-frontend-domain.com
# ... API keys (email for credentials)
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
NODE_ENV=production
```

### Deployment Platforms
- **Railway** - Automatic Docker deployments
- **Vercel** - Frontend deployment
- **Render** - Full-stack deployment
- **Heroku** - Container deployments

## 📧 Getting Started

1. **Clone the repository**
2. **Email project owner for API credentials**
3. **Follow Docker setup above (recommended)**
4. **Start chatting and finding deals!**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is private. Please contact the project owner for licensing information. 