.PHONY: up down reset test eval validate clean help smoke verify pipeline

help:
	@echo "Available commands:"
	@echo "  make pipeline - Run automated data ingestion, validation, and chunking pipeline"
	@echo "  make up       - Start all services with docker-compose"
	@echo "  make down     - Stop all services"
	@echo "  make seed     - Load seed data into database"
	@echo "  make reset    - Reset database to clean seed state"
	@echo "  make test     - Run automated test suite"
	@echo "  make smoke    - Run seeded-student API and browser smoke tests"
	@echo "  make eval     - Run student profile evaluation harness"
	@echo "  make validate - Run knowledge base integrity validator"
	@echo "  make verify   - Run full end-to-end automated verification suite"

pipeline:
	python run_pipeline.py

up:
	docker compose up --build

down:
	docker compose down

seed:
	python -m backend.db.seed_loader --reset

reset:
	python -m backend.db.seed_loader --reset

test:
	python scripts/run_tests.py

smoke:
	python scripts/run_smoke.py

eval:
	python scripts/evaluate.py

validate:
	python scripts/validate_kb.py

verify:
	python scripts/verify.py

clean:
	rm -rf data/*.db data/*.sqlite __pycache__ backend/**/__pycache__ tests/__pycache__
