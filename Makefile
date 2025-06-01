.PHONY: help start stop restart restart-celery sync-spotify-data update-spotify-tokens ruff-fix gen-env

help:
	@echo "Available commands:"
	@echo "  make start                # Start all services with Docker Compose"
	@echo "  make stop                 # Stop all services"
	@echo "  make restart              # Restart all services"
	@echo "  make restart-celery       # Restart only the Celery service"
	@echo "  make ruff-fix             # Run Ruff with --fix"
	@echo "  make gen-env              # Generate .env from env.sample with FERNET_KEY"

start:
	docker-compose up -d

stop:
	docker-compose down

restart:
	docker-compose down
	docker-compose up -d

restart-celery:
	docker-compose restart celery

ruff-fix:
	cd project && ruff check . --fix

gen-env:
	cp env.sample .env
	@python3 -c "from cryptography.fernet import Fernet; print('FERNET_KEY=' + Fernet.generate_key().decode())" >> .env
	@echo ".env generated with FERNET_KEY"