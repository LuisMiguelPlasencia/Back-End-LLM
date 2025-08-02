.PHONY: help install test run clean docker-build docker-run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	poetry install

install-dev: ## Install development dependencies
	poetry install --with dev

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=app --cov-report=html

lint: ## Run linting
	poetry run black app tests
	poetry run isort app tests
	poetry run flake8 app tests

type-check: ## Run type checking
	poetry run mypy app

format: ## Format code
	poetry run black app tests
	poetry run isort app tests

run: ## Run the development server
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

db-migrate: ## Run database migrations
	poetry run alembic upgrade head

db-revision: ## Create new migration
	poetry run alembic revision --autogenerate -m "$(message)"

db-reset: ## Reset database
	poetry run alembic downgrade base
	poetry run alembic upgrade head

setup: ## Initial setup
	cp env.example .env
	poetry install
	poetry run alembic upgrade head

docker-build: ## Build Docker image
	docker build -t speech-to-text-backend .

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-stop: ## Stop Docker Compose
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

clean: ## Clean up
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov .pytest_cache

logs: ## View application logs
	tail -f logs/app.log

health: ## Check application health
	curl -f http://localhost:8000/api/v1/health/ || echo "Application is not healthy"

docs: ## Generate API documentation
	poetry run python -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8000)" &
	sleep 5
	curl http://localhost:8000/docs
	pkill -f uvicorn 