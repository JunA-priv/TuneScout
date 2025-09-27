.PHONY: setup up-deps dev migrate down win-up dev-compose

setup:
	uv sync

up-deps:
	docker compose up -d db redis

dev:
	uv run uvicorn apps.api.main:app --reload

migrate:
	uv run alembic upgrade head

down:
	docker compose down

win-up:
	docker compose up --build -d

dev-compose:
	docker compose -f compose.yaml -f compose.dev.yaml up --build
