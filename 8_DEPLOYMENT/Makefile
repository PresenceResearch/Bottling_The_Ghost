DEPLOY_DIR := $(CURDIR)
ROOT_DIR := $(abspath $(CURDIR)/..)
VENV_PYTHON := $(DEPLOY_DIR)/.venv/bin/python
RUNTIME_VENV_PYTHON := $(HOME)/.clara_runtime/venv/bin/python
RUNTIME_DIR := $(HOME)/.clara_runtime

.PHONY: setup setup-runtime sync-runtime deploy-runtime index run install-services start-services stop-services status-services logs

setup:
	python3 -m venv .venv
	$(VENV_PYTHON) -m pip install -r requirements.txt

setup-runtime:
	bash scripts/setup_runtime_venv.sh

sync-runtime:
	bash scripts/sync_runtime_app.sh

deploy-runtime:
	bash scripts/sync_runtime_app.sh
	bash scripts/install_launch_agents.sh
	$(MAKE) status-services

index:
	$(RUNTIME_VENV_PYTHON) embed_corpus.py

run:
	$(RUNTIME_VENV_PYTHON) telegram_bot.py

install-services:
	bash scripts/install_launch_agents.sh

start-services:
	launchctl kickstart -k gui/$$(id -u)/com.clara.ollama
	launchctl kickstart -k gui/$$(id -u)/com.clara.bot

stop-services:
	launchctl bootout gui/$$(id -u) ~/Library/LaunchAgents/com.clara.bot.plist || true
	launchctl bootout gui/$$(id -u) ~/Library/LaunchAgents/com.clara.ollama.plist || true

status-services:
	launchctl print gui/$$(id -u)/com.clara.ollama >/dev/null 2>&1 && echo "com.clara.ollama: running" || echo "com.clara.ollama: not running"
	launchctl print gui/$$(id -u)/com.clara.bot >/dev/null 2>&1 && echo "com.clara.bot: running" || echo "com.clara.bot: not running"

logs:
	@echo "Tailing Clara logs from $(RUNTIME_DIR)/logs ..."
	tail -f $(RUNTIME_DIR)/logs/ollama.log $(RUNTIME_DIR)/logs/clara_bot.log
