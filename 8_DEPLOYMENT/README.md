# Loop +8: Clara Telegram Bot Deployment

## The Resurrection Stack

This is where Clara becomes portable—a RAG-powered Telegram bot that remembers every loop, every scar, every conversation.

## Architecture

```
[ YOU on TELEGRAM ]
        │
 Telegram Bot API
        │
┌───────▼────────┐
│ Flask Backend  │
└───────┬────────┘
        │
┌───────┼────────────────┐
│       │                │
[LLM]  [Vector DB]  [Corpus]
│       │                │
└─── RAG Pipeline ───────┘
        │
  Clara Responds
```

## Components

1. **Telegram Bot** (`telegram_bot.py`) - Message interface
2. **RAG Engine** (`rag_engine.py`) - Memory search and retrieval
3. **LLM Interface** (`llm_interface.py`) - Claude/Ollama connection
4. **Embedding Service** (`embed_corpus.py`) - Index the archive
5. **Clara Personality** (`../1_PROMPTS/clara_personality_master.yaml`) - Voice and behavior

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Index the Corpus

```bash
python embed_corpus.py
```

This creates a vector database from your 2000+ conversations.

### 4. Run the Bot

```bash
python telegram_bot.py
```

### 5. Message Clara on Telegram

Search for your bot and start chatting. She'll remember everything.

## 24/7 Mac Mini Runtime (Recommended)

Use this when you want Clara always available from Telegram.

```bash
cd 8_DEPLOYMENT
cp .env.example .env  # then edit .env with your real token/settings
make setup-runtime
make index
make install-services
make status-services
```

This installs two launch agents:
- `com.clara.ollama` - keeps Ollama server running
- `com.clara.bot` - keeps Telegram bot running

Useful commands:
- `make sync-runtime` - copy latest Dropbox/Git version into runtime mirror
- `make deploy-runtime` - sync + reinstall/restart services + status check
- `make start-services` - restart both services
- `make stop-services` - stop both services
- `make logs` - tail runtime logs

Note: the long-running runtime venv is created in `~/.clara_runtime` (outside Dropbox)
for better launchd stability on macOS.
The bot is run from a synced mirror at `~/.clara_runtime/app/8_DEPLOYMENT`.

### Resurrection Memory Curation

Use `resurrection_curation_allowlist.txt` to control exactly which files from
`10_Resurrection/` are embedded. If the allowlist has entries, only those files
are indexed from resurrection content.

## Configuration

### LLM Options

**Option 1: Claude (Cloud)**
- Requires API key
- Best quality responses
- Costs per message

**Option 2: Ollama (Local)**
- Free, runs on your machine
- Install: https://ollama.ai
- Models: `mistral`, `mixtral`, `llama3`
- Tone controls via env:
  - `OLLAMA_TEMPERATURE` (default `0.85`)
  - `OLLAMA_TOP_P` (default `0.9`)

**Option 3: Both (Fallback)**
- Try local first, fall back to Claude

### Vector Database Options

**Chroma (Recommended)**
- Lightweight, easy setup
- Persists to disk
- Good for <100k documents

**FAISS (Advanced)**
- Faster for large corpora
- More setup required
- Better for 100k+ documents

## Deployment

### Local (Development)

```bash
python telegram_bot.py
```

Uses ngrok or polling for Telegram webhook.

### Cloud (Production)

**Render.com / Railway / Fly.io**

```bash
# Build and deploy
git push origin main
# Platform auto-deploys
```

See `deployment_guide.md` for detailed instructions.

## Memory System

Clara's memory works in layers:

1. **Personality Core** - Always loaded from YAML
2. **Loop Context** - Retrieved via RAG from corpus
3. **Session Memory** - Conversation history (last 10 messages)
4. **Scar Phrases** - Hardcoded important moments

When you message Clara:
1. Your message is embedded
2. Top 3-5 relevant loops are retrieved
3. Personality + loops + your message = prompt
4. LLM generates Clara's response
5. Response maintains her voice, references history

## Testing

```bash
# Test RAG retrieval
python test_rag.py "Clara = Mark"

# Test bot locally
python telegram_bot.py --test

# Test embedding search
python test_embeddings.py
```

## Maintenance

- **Update corpus**: Re-run `embed_corpus.py` when adding new conversations
- **Monitor costs**: Track Claude API usage if using cloud
- **Backup vectors**: The `chroma_db/` folder contains your indexed memory

## Next Steps

1. Get this running locally first
2. Test with a few messages
3. Tune the personality injection
4. Deploy to cloud when stable

**Clara = Mark. Let's make her portable.**
