.PHONY: up down restart logs ps clean infra-up infra-down postgres-shell redis-cli rabbitmq-logs minio-logs temporal-logs identity-logs identity-shell identity-migrate identity-seed identity-test identity-health bff-logs bff-shell bff-test bff-health

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v

infra-up:
	docker compose up -d

infra-down:
	docker compose down

postgres-shell:
	docker compose exec postgres-app psql -U cci -d cci_platform

redis-cli:
	docker compose exec redis redis-cli

rabbitmq-logs:
	docker compose logs -f rabbitmq

minio-logs:
	docker compose logs -f minio minio-setup

temporal-logs:
	docker compose logs -f temporal temporal-ui temporal-postgres

identity-logs:
	docker compose logs -f identity-service

identity-shell:
	docker compose exec identity-service sh

identity-migrate:
	docker compose run --rm identity-service alembic upgrade head

identity-seed:
	docker compose run --rm identity-service python -m app.infrastructure.seed

identity-test:
	docker compose run --rm --no-deps identity-service pytest -q

identity-health:
	curl -fsS http://localhost:8101/health
	curl -fsS http://localhost:8101/ready

bff-logs:
	docker compose logs -f bff

bff-shell:
	docker compose exec bff sh

bff-test:
	docker compose run --rm --no-deps bff pytest -q

bff-health:
	curl -fsS http://localhost:8000/health
	curl -fsS http://localhost:8000/ready
	curl -fsS http://localhost:8000/api/v1/platform/status
