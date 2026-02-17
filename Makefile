PYTHON := .venv/bin/python
PIP := $(PYTHON) -m pip

.PHONY: setup smoke upgrade-pip

setup:
	python3 -m venv .venv
	$(PIP) install -r requirements.txt

smoke:
	$(PYTHON) smoke_test_ollama.py

upgrade-pip:
	$(PIP) install --upgrade pip
