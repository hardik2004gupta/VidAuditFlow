.PHONY: setup dev-backend dev-frontend test test-backend test-frontend \
	lint lint-backend lint-frontend format coverage build migrate clean help

help:
	@echo "VidAuditFlow -- common development commands"
	@echo ""
	@echo "  make setup          Install backend (uv) and frontend (npm) dependencies"
	@echo "  make dev-backend    Run the FastAPI backend with auto-reload"
	@echo "  make dev-frontend   Run the Next.js frontend dev server"
	@echo "  make test           Run backend and frontend test suites"
	@echo "  make test-backend   Run backend tests only (pytest)"
	@echo "  make test-frontend  Run frontend tests only (vitest)"
	@echo "  make coverage       Run both test suites with coverage reports"
	@echo "  make lint           Run backend (ruff) and frontend (eslint) linters"
	@echo "  make format         Auto-format backend (ruff) and frontend (prettier)"
	@echo "  make build          Build the frontend for production"
	@echo "  make migrate        Apply database migrations (alembic upgrade head)"
	@echo "  make clean          Remove caches and build artifacts"

setup:
	uv sync --all-groups
	cd frontend && npm install

dev-backend:
	uv run uvicorn backend.src.api.main:app --reload

dev-frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	uv run pytest

test-frontend:
	cd frontend && npm test

coverage:
	uv run pytest --cov --cov-report=term-missing
	cd frontend && npm run test:coverage

lint: lint-backend lint-frontend

lint-backend:
	uv run ruff check .

lint-frontend:
	cd frontend && npm run lint

format:
	uv run ruff format .
	uv run ruff check --fix .
	cd frontend && npm run format

build:
	cd frontend && npm run build

migrate:
	uv run alembic upgrade head

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage
	rm -rf frontend/.next frontend/coverage
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
