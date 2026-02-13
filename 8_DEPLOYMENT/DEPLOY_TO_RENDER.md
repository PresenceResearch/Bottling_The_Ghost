# Deploying Clara to Render.com

## Step 1: Prepare for Deployment

First, we need to create a few files that tell Render how to run Clara.

### Create `Procfile`
This tells Render how to start the bot:

```
web: python telegram_bot.py
```

### Create `render.yaml` (optional but recommended)
Configuration for Render:

```yaml
services:
  - type: web
    name: clara-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python telegram_bot.py
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: LLM_PROVIDER
        value: claude
      - key: CLAUDE_API_KEY
        sync: false
      - key: TOP_K_RESULTS
        value: 3
```

### Update `requirements.txt`
Make sure all dependencies are listed (already done).

---

## Step 2: Sign Up for Render

1. Go to: https://render.com
2. Click "Get Started"
3. Sign up with GitHub (easiest way)
4. Authorize Render to access your repos

---

## Step 3: Create a New Web Service

1. Click "New +" → "Web Service"
2. Connect to your GitHub repository: `PresenceResearch/Bottling_The_Ghost`
3. Configure:
   - **Name:** `clara-bot`
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Root Directory:** `8_DEPLOYMENT`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python telegram_bot.py`
   - **Plan:** Free (for now)

---

## Step 4: Set Environment Variables

In Render dashboard, go to "Environment" and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
LLM_PROVIDER=claude
CLAUDE_API_KEY=your_claude_key_here
EMBEDDING_MODEL=all-MiniLM-L6-v2
TOP_K_RESULTS=3
CORPUS_PATH=../6_CORPUS
PERSONALITY_PATH=../1_PROMPTS/clara_personality_master.yaml
VECTOR_DB_PATH=./chroma_db
```

**Important:** Mark these as "Secret" so they're encrypted.

---

## Step 5: Handle the Corpus

**Problem:** The corpus is 2GB+ and can't be deployed directly.

**Solution:** Two options:

### Option A: Deploy without corpus (Claude-only, no RAG)
- Faster deployment
- No memory search
- Clara responds based on personality only
- Good for testing

### Option B: Use cloud storage for corpus
- Upload corpus to AWS S3 / Google Cloud Storage
- Download on startup
- Full memory search
- Takes longer to start

**For now, let's start with Option A** (Claude-only), then add RAG later.

---

## Step 6: Deploy

1. Click "Create Web Service"
2. Render will:
   - Clone your repo
   - Install dependencies
   - Start the bot
3. Watch the logs for "Clara bot starting..."
4. If successful, the bot is now online 24/7!

---

## Step 7: Test

Message @MPM410_bot on Telegram. She should respond even if your laptop is off.

---

## Troubleshooting

**"Build failed"**
- Check logs for missing dependencies
- Make sure `requirements.txt` is complete

**"Bot not responding"**
- Check environment variables are set
- Look for errors in logs
- Make sure bot token is correct

**"Out of memory"**
- Free tier has 512MB RAM
- Reduce `TOP_K_RESULTS` to 2
- Use smaller embedding model

---

## Next Steps After Deployment

1. **Add RAG with cloud storage** - So Clara has full memory
2. **Upgrade to paid tier** - For better performance ($7/month)
3. **Set up monitoring** - Get alerts if bot goes down
4. **Auto-deploy on git push** - Update Clara by pushing to GitHub

---

**Cost breakdown:**
- Render Free Tier: $0/month (500 hours, enough for 24/7)
- Claude API: ~$5-10/month depending on usage
- **Total: $5-10/month**

---

Let me know when you're ready to start, and I'll walk you through each step!
