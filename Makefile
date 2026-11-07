.PHONY: up down init-db test lint format

up:
	docker compose up -d

down:
	docker compose down

init-db:
	python scripts/init_db.py

test:
	pytest tests/test_smoke.py -v

lint:
	ruff check src scripts migrations

format:
	ruff format src scripts