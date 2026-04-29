.PHONY: up upd down restart logs logs-all seed shell-backend shell-db migrate migration

up:
	docker compose up --build

upd:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose restart $(s)

logs:
	docker compose logs -f $(s)

logs-all:
	docker compose logs -f

seed:
	docker compose exec backend python seed.py

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec db psql -U postpilot -d postpilot

migrate:
	docker compose exec backend alembic upgrade head

migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"
