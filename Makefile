.PHONY: setup up logs test lint format migrate migration clean

setup:
	@if [ -f .env ]; then \
		echo ".env already exists; left unchanged"; \
	else \
		password=$$(openssl rand -hex 32); \
		sed "s/^POSTGRES_PASSWORD=$$/POSTGRES_PASSWORD=$$password/" .env.example > .env; \
		echo "Created .env with a random PostgreSQL password"; \
	fi

up:
	docker compose up --build

logs:
	docker compose logs -f backend frontend postgres

test:
	docker compose run --rm backend pytest -q
	cd frontend && npm test

lint:
	docker compose run --rm backend ruff check app tests
	docker compose run --rm backend ruff format --check app tests
	cd frontend && npm run lint

format:
	docker compose run --rm backend ruff check --fix app tests
	docker compose run --rm backend ruff format app tests
	cd frontend && npm run format

migrate:
	docker compose run --rm backend alembic upgrade head

migration:
	docker compose run --rm backend alembic revision --autogenerate -m "$(name)"

clean:
	docker compose down

