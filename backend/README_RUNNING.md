# Running the Agent System

## ✅ **Correct Way to Run**

Always run Python from the `backend/` directory so that `app` is importable:

```bash
# From the backend directory
cd backend/

# Run the example
python -m app.modules.example_usage

# Or run the test
python test_agent.py

# Or run the convenient wrapper
python run_agent_example.py

# Start the main server
uvicorn app.main:app --reload
```

## 🎯 **Import Structure**

All imports should start from `app`:

```python
# ✅ Good - relative imports within app
from .agent import Agent, Tool, LLM
from ..config import GEMINI_API_KEY

# ✅ Good - absolute imports from app
from app.modules.agent import Agent, Tool, LLM
from app.config import GEMINI_API_KEY

# ❌ Bad - sys.path manipulation
import sys
sys.path.insert(0, some_path)
```

## 📁 **Directory Structure**

```
backend/
├── app/
│   ├── config.py              # Centralized config
│   ├── main.py               # FastAPI app
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── agent.py          # Core agent classes
│   │   ├── streaming_agent.py # Streaming version
│   │   └── example_usage.py  # Example/demo
│   ├── routes/
│   └── utils/
├── test_agent.py             # Test script
├── run_agent_example.py      # Convenience runner
└── .env                      # Environment variables
```

## 🚀 **Testing**

```bash
cd backend/
python test_agent.py           # Basic functionality test
python run_agent_example.py    # Full example with tools
``` 