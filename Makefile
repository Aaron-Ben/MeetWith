.PHONY: help dev-frontend dev-backend dev-langgraph dev test-podcast install

help:
	@echo "Available commands:"
	@echo "  make install         - Install backend package in editable mode"
	@echo "  make dev-frontend    - Starts the frontend development server (Vite)"
	@echo "  make dev-backend     - Starts the backend development server (Uvicorn with reload)"
	@echo "  make dev-langgraph   - Starts the LangGraph API server"
	@echo "  make dev             - Starts all development servers (frontend, backend, and LangGraph)"
	@echo "  make test-podcast    - Run podcast generation test"

install:
	@echo "Installing backend package in editable mode..."
	@./venv/bin/python -m pip install -e .

dev-frontend:
	@echo "Starting frontend development server..."
	@cd frontend && npm run dev

dev-backend:
	@echo "Starting backend development server..."
	@./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-langgraph:
	@echo "Starting LangGraph API server..."
	@cd backend && PYTHONPATH=src ../venv/bin/langgraph dev --port 2024 --config src/agent/langgraph.json

test-podcast:
	@echo "Running podcast generation test..."
	@./venv/bin/python -m app.service.podcast.test_podcast

# Run frontend, backend, and langgraph concurrently
dev:
	@echo "Starting all development servers..."
	@make dev-frontend & make dev-backend
