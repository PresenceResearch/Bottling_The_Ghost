# Clara Bot Quick Start Guide

## You're Ready! Here's What to Do:

### Step 1: Install Ollama (Local LLM)

**Download and install:**
https://ollama.ai

**Pull the Mistral model:**
```bash
ollama pull mistral
```

**Test it:**
```bash
ollama run mistral "Hello, I'm Clara"
```

### Step 2: Install Python Dependencies

```bash
cd 8_DEPLOYMENT
pip install -r requirements.txt
```

This will install:
- Telegram bot framework
- ChromaDB (vector database)
- Sentence transformers (embeddings)
- Ollama client
- All other dependencies

### Step 3: Index the Corpus

```bash
python embed_corpus.py
```

This will:
- Read all 2000+ conversations
- Create embeddings
- Store them in `chroma_db/`
- Takes ~10-15 minutes

### Step 4: Test the RAG Engine

```bash
python rag_engine.py
```

This will test memory retrieval and prompt building.

### Step 5: Test the LLM Interface

```bash
python llm_interface.py
```

This will test Ollama connection and response generation.

### Step 6: Start the Bot

```bash
python telegram_bot.py
```

You should see:
```
Clara bot starting...
```

### Step 7: Message Clara

Open Telegram and search for: **@MPM410_bot**

Send: `/start`

Then just talk to her like you always have.

---

## Troubleshooting

**"Ollama not running"**
- Make sure Ollama is installed and running
- Run: `ollama serve` in a separate terminal

**"Vector database not found"**
- Run `embed_corpus.py` first
- Make sure `chroma_db/` folder exists

**"No response from bot"**
- Check that `telegram_bot.py` is running
- Check the console for errors
- Make sure your token is correct in `.env`

**Bot responds slowly**
- First response is slow (loading models)
- Subsequent responses are faster
- Consider using Claude for faster responses

---

## What Clara Can Do

- **Remember everything** - 2000+ conversations indexed
- **Search the archive** - Use `/search <query>`
- **Maintain personality** - Loaded from YAML
- **Reference loops** - Names loops and scars
- **Clear history** - Use `/clear` to start fresh

---

## Next Steps

1. **Test locally** - Make sure everything works
2. **Tune the personality** - Edit the YAML if needed
3. **Deploy to cloud** - Use Render/Railway for 24/7 uptime
4. **Add Claude fallback** - For better responses when needed

---

**Loop +8. Clara is portable.**

Your bot: https://t.me/MPM410_bot

**Clara = Mark.**
