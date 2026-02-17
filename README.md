# Clara_Core

Core repository for Clara personality system, prompts, and integration configurations.

## Structure

- **1_PROMPTS**: Core personality definitions, affirmations, and behavioral patterns
- **2_ARCHIVE**: Historical data and raw loop exports
- **3_INTEGRATIONS**: Integration configurations for Cursor, LlamaIndex, and Ollama
- **4_VALIDATION**: Test cases and validation metrics
- **5_DEPLOY**: Deployment and runtime configurations

## Local Runtime Quickstart

1. Create and activate a virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Install dependencies:
   - `python -m pip install -r requirements.txt`
3. Start Ollama in another terminal:
   - `ollama serve`
4. Run the smoke test:
   - `python smoke_test_ollama.py`

## Makefile Shortcuts

- `make setup` - Create `.venv` and install dependencies
- `make smoke` - Run `smoke_test_ollama.py`
- `make upgrade-pip` - Upgrade pip inside `.venv`

