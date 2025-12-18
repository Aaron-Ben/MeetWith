.PHONY: help dev-frontend dev-backend dev-langgraph dev

help:
	@echo "Available commands:"
	@echo "  make dev-frontend    - Starts the frontend development server (Vite)"
	@echo "  make dev-backend     - Starts the backend development server (Uvicorn with reload)"
	@echo "  make dev-langgraph   - Starts the LangGraph API server"
	@echo "  make dev             - Starts all development servers (frontend, backend, and LangGraph)"

dev-frontend:
	@echo "Starting frontend development server..."
	@cd frontend && npm run dev

dev-backend:
	@echo "Starting backend development server..."
	@cd backend && PYTHONPATH=src ../venv/bin/python -m uvicorn src.agent.app:app --reload --host 0.0.0.0 --port 8000

dev-langgraph:
	@echo "Starting LangGraph API server..."
	@cd backend && PYTHONPATH=src ../venv/bin/langgraph dev --port 2024 --config src/agent/langgraph.json

# Run frontend, backend, and langgraph concurrently
dev:
	@echo "Starting all development servers..."
	@make dev-frontend & make dev-backend & make dev-langgraph
