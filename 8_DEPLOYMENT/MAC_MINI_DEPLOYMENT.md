# Mac Mini Deployment - Step by Step

**Goal:** Deploy Clara bot permanently on Mac Mini (always-on, local, private)

**Time:** ~1 hour

---

## Pre-flight Check

- [ ] Mac Mini is powered on and connected to network
- [ ] You can access it (either sit at it, or SSH from Windows)
- [ ] Dropbox is installed (so Clara_Core folder syncs)
- [ ] You have your Telegram bot token ready

---

## Step 1: Mac Mini System Setup (10 min)

### Open Terminal on Mac Mini

**Option A:** Sit at the Mac and open Terminal app  
**Option B:** SSH from Windows: `ssh username@mac-mini-ip-address`

### Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Install Python and Git

```bash
brew install python@3.11 git
```

---

## Step 2: Install Ollama (5 min)

### Download and install

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Pull Mistral model

```bash
ollama pull mistral
```

This downloads the AI model (~4GB). Wait for it to finish.

### Test Ollama

```bash
ollama run mistral "Hello, I'm Clara"
```

You should see a response. Press Ctrl+D to exit.

---

## Step 3: Set Up Clara Repository (5 min)

### Navigate to Dropbox folder (if synced)

```bash
cd ~/Dropbox/Clara_Core/8_DEPLOYMENT
```

**OR** if Dropbox isn't synced, clone from GitHub:

```bash
cd ~
git clone https://github.com/PresenceResearch/Bottling_The_Ghost.git clara
cd clara/8_DEPLOYMENT
```

### Create Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

This takes 5-10 minutes. Let it run.

---

## Step 4: Configure Environment (2 min)

### Create .env file

```bash
cp .env.example .env
nano .env
```

### Set these values:

```
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
LLM_PROVIDER=ollama
OLLAMA_MODEL=mistral
TOP_K_RESULTS=5
CORPUS_PATH=../6_CORPUS
PERSONALITY_PATH=../1_PROMPTS/clara_personality_master.yaml
VECTOR_DB_PATH=./chroma_db
```

Save with: Ctrl+O, Enter, Ctrl+X

---

## Step 5: Index the Corpus (15 min)

### Run embedding script

```bash
python embed_corpus.py
```

This will:
- Read all 2000+ conversations
- Create vector embeddings
- Store in `chroma_db/` folder
- Takes 10-15 minutes

**Go get coffee. This is the longest step.**

---

## Step 6: Test the Bot (5 min)

### Start bot manually first

```bash
python telegram_bot.py
```

You should see: `Clara bot starting...`

### Test on Telegram

Open Telegram, message @MPM410_bot

Send: "hey clara, you there?"

She should respond.

### Stop the bot

Press Ctrl+C in terminal

---

## Step 7: Auto-Start on Boot (10 min)

### Create LaunchAgent directory

```bash
mkdir -p ~/Library/LaunchAgents
```

### Create plist file

```bash
nano ~/Library/LaunchAgents/com.clara.bot.plist
```

### Paste this (CHANGE YOUR_USERNAME):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.clara.bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/Dropbox/Clara_Core/8_DEPLOYMENT/venv/bin/python</string>
        <string>/Users/YOUR_USERNAME/Dropbox/Clara_Core/8_DEPLOYMENT/telegram_bot.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/Dropbox/Clara_Core/8_DEPLOYMENT</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Dropbox/Clara_Core/logs/clara_bot.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Dropbox/Clara_Core/logs/clara_bot_error.log</string>
</dict>
</plist>
```

Save with: Ctrl+O, Enter, Ctrl+X

### Create logs folder

```bash
mkdir -p ~/Dropbox/Clara_Core/logs
```

### Load the service

```bash
launchctl load ~/Library/LaunchAgents/com.clara.bot.plist
```

### Check if it's running

```bash
launchctl list | grep clara
ps aux | grep telegram_bot
```

You should see the process running.

---

## Step 8: Verify & Monitor (5 min)

### Test from Telegram

Message @MPM410_bot - she should respond

### View logs

```bash
tail -f ~/Dropbox/Clara_Core/logs/clara_bot.log
```

Press Ctrl+C to stop viewing logs.

### Check bot is running

```bash
ps aux | grep telegram_bot
```

---

## Updating Clara Later

When you push changes from Windows:

```bash
# SSH into Mac Mini
cd ~/Dropbox/Clara_Core
git pull origin main

# Restart bot
launchctl unload ~/Library/LaunchAgents/com.clara.bot.plist
launchctl load ~/Library/LaunchAgents/com.clara.bot.plist
```

---

## Troubleshooting

**"Ollama not found"**
- Run: `brew install ollama`

**"Bot not responding"**
- Check logs: `tail -f ~/Dropbox/Clara_Core/logs/clara_bot_error.log`
- Check bot is running: `ps aux | grep telegram_bot`

**"ModuleNotFoundError"**
- Activate venv: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

**"ChromaDB error"**
- Delete and rebuild: `rm -rf chroma_db && python embed_corpus.py`

---

## Success Checklist

- [ ] Ollama installed and Mistral model downloaded
- [ ] Python dependencies installed
- [ ] .env file configured with bot token
- [ ] Corpus indexed (chroma_db folder exists)
- [ ] Bot responds on Telegram when run manually
- [ ] LaunchAgent configured and loaded
- [ ] Bot auto-starts and stays running
- [ ] Logs are being written

---

**When all checked: Clara is permanently deployed! 🎉**

**Loop +8. The mirror has a permanent home.**
