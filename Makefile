.PHONY: up down restart logs ps build migrate seed test lint format reset clean infra-up infra-down infra-check create-buckets create-schemas packages-test postgres-shell redis-cli rabbitmq-logs minio-logs temporal-logs identity-logs identity-shell identity-migrate identity-seed identity-test identity-health client-logs client-shell client-migrate client-test client-health document-logs document-shell document-migrate document-test document-health parser-logs parser-shell parser-test parser-health bff-logs bff-shell bff-test bff-health

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

build:
	docker compose build

migrate: identity-migrate client-migrate document-migrate

seed: identity-seed

packages-test:
	pytest packages

test: packages-test identity-test client-test document-test parser-test bff-test

lint:
	docker compose config > /dev/null
	cd apps/web && npm run lint

format:
	cd apps/web && npm run lint -- --fix

reset:
	sh infra/scripts/reset-local-env.sh

clean:
	sh infra/scripts/reset-local-env.sh

infra-up:
	docker compose up -d

infra-down:
	docker compose down

infra-check:
	sh infra/scripts/check-infra.sh

create-buckets:
	docker compose run --rm minio-setup

create-schemas:
	sh infra/scripts/create-postgres-schemas.sh

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

client-logs:
	docker compose logs -f client-service

client-shell:
	docker compose exec client-service sh

client-migrate:
	docker compose run --rm client-service alembic upgrade head

client-test:
	docker compose --profile test run --rm client-service-test

client-health:
	curl -fsS http://localhost:8102/health
	curl -fsS http://localhost:8102/ready

document-logs:
	docker compose logs -f document-service

document-shell:
	docker compose exec document-service sh

document-migrate:
	docker compose run --rm document-service alembic upgrade head

document-test:
	docker compose --profile test run --rm document-service-test

document-health:
	curl -fsS http://localhost:8110/health
	curl -fsS http://localhost:8110/ready

parser-logs:
	docker compose logs -f parser-worker

parser-shell:
	docker compose exec parser-worker sh

parser-test:
	docker compose run --rm --no-deps parser-worker pytest -q

parser-health:
	curl -fsS http://localhost:8121/health
	curl -fsS http://localhost:8121/ready

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
