.DEFAULT_GOAL := help

PYTHON ?= python3
PORT ?= 8000
VENV := .venv
PY := $(VENV)/bin/python

.PHONY: help setup run test clean

help: ## Show available commands
	@printf '\nDaily Java\n\n'
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  make %-10s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@printf '\nStart here: make run\n\n'

$(PY):
	$(PYTHON) -m venv $(VENV)

$(VENV)/.app-ready: requirements.txt $(PY)
	$(PY) -m pip install -r requirements.txt
	@touch $@

$(VENV)/.dev-ready: requirements-dev.txt $(VENV)/.app-ready
	$(PY) -m pip install -r requirements-dev.txt
	@touch $@

setup: $(VENV)/.app-ready ## Create the virtual environment and install app dependencies

run: setup ## Set up and start the app at http://127.0.0.1:8000
	PYTHONDONTWRITEBYTECODE=1 $(PY) -m uvicorn app.main:app --reload --host 127.0.0.1 --port $(PORT)

test: $(VENV)/.dev-ready ## Install test dependencies and run the tests
	PYTHONDONTWRITEBYTECODE=1 $(PY) -m pytest -q

clean: ## Remove the virtual environment and test cache; keep saved results
	rm -rf $(VENV) .pytest_cache
