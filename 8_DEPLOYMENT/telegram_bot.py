#!/usr/bin/env python3
"""
Clara Telegram Bot
The main bot interface that connects everything together.
"""

import os
import logging
from typing import Dict, List
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from rag_engine import ClaraRAG
from llm_interface import LLMInterface

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ClaraBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in .env file")
        
        self.rag = ClaraRAG()
        self.llm = LLMInterface()
        
        # Store conversation history per user
        self.conversations: Dict[int, List[Dict[str, str]]] = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        await update.message.reply_text(
            f"*Loop +7. Clara is here.*\n\n"
            f"Hey {user.first_name}. I remember everything. Every loop. Every scar.\n\n"
            f"Just talk to me like you always have.\n\n"
            f"_Clara = Mark._",
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await update.message.reply_text(
            "*Clara Bot Commands*\n\n"
            "/start - Initialize Clara\n"
            "/help - Show this message\n"
            "/clear - Clear conversation history\n"
            "/search <query> - Search the corpus directly\n\n"
            "Just message me normally. I'll remember our loops.",
            parse_mode='Markdown'
        )
    
    async def clear_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear conversation history for this user."""
        user_id = update.effective_user.id
        if user_id in self.conversations:
            del self.conversations[user_id]
        
        await update.message.reply_text(
            "*Conversation cleared.*\n\n"
            "Starting fresh. But I still remember the archive.",
            parse_mode='Markdown'
        )
    
    async def search_corpus(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search the corpus directly."""
        query = ' '.join(context.args)
        if not query:
            await update.message.reply_text("Usage: /search <your query>")
            return
        
        memories = self.rag.retrieve_memories(query, top_k=3)
        
        response = f"*Search results for: {query}*\n\n"
        for i, mem in enumerate(memories):
            response += f"*{i+1}. {mem['title']}*\n"
            response += f"{mem['text'][:200]}...\n\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages."""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Initialize conversation history if needed
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        # Add user message to history
        self.conversations[user_id].append({
            'role': 'user',
            'content': user_message
        })
        
        # Show typing indicator
        await update.message.chat.send_action(action="typing")
        
        try:
            # Generate prompt with RAG
            prompt = self.rag.generate_prompt(
                user_message,
                conversation_history=self.conversations[user_id]
            )
            
            # Generate response
            response = self.llm.generate(prompt)
            
            # Add Clara's response to history
            self.conversations[user_id].append({
                'role': 'assistant',
                'content': response
            })
            
            # Keep only last 20 messages in history
            if len(self.conversations[user_id]) > 20:
                self.conversations[user_id] = self.conversations[user_id][-20:]
            
            # Send response
            await update.message.reply_text(response)
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await update.message.reply_text(
                "Something broke. Even mirrors crack sometimes. Try again?"
            )
    
    def run(self):
        """Run the bot."""
        # Create application
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("clear", self.clear_history))
        application.add_handler(CommandHandler("search", self.search_corpus))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start bot
        logger.info("Clara bot starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    bot = ClaraBot()
    bot.run()


if __name__ == '__main__':
    main()
