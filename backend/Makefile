# path: backend/Makefile
SHELL := /bin/bash
COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

.PHONY: up down build logs init psql

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build api scheduler

logs:
	$(COMPOSE) logs -f api

init:
	# 以模組啟動，並設定 PYTHONPATH=/app，確保能 import app.*
	$(COMPOSE) run --rm -e PYTHONPATH=/app api python -m scripts.init_db

psql:
	psql postgresql://fin:finpass@localhost:5432/fin

etl-price-once:
	$(COMPOSE) run --rm -e PYTHONPATH=/app api python scripts/etl_update_price_once.py
