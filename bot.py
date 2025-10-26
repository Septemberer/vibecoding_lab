#!/usr/bin/env python3
"""
Telegram News Bot

A Telegram bot for managing news articles with features like:
- Adding news with keywords
- Daily news digest at 7:30 Moscow time
- Liking news articles
- Searching news by keywords

Author: AI Assistant
"""

import json
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler
)
from telegram.error import TelegramError
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_FILE = 'news_bot_database.json'
MOSCOW_TIMEZONE = pytz.timezone('Europe/Moscow')

class NewsBotDatabase:
    """Handles all database operations for the news bot"""
    
    def __init__(self, db_file: str = DATABASE_FILE):
        self.db_file = db_file
        self.data = self._load_database()
    
    def _load_database(self) -> Dict[str, Any]:
        """Load database from JSON file or create new one"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading database: {e}")
                return self._create_empty_database()
        else:
            return self._create_empty_database()
    
    def _create_empty_database(self) -> Dict[str, Any]:
        """Create empty database structure"""
        return {
            "users": [],
            "news": [],
            "likes": [],
            "counters": {
                "user_id": 0,
                "news_id": 0,
                "like_id": 0
            }
        }
    
    def _save_database(self) -> bool:
        """Save database to JSON file"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"Error saving database: {e}")
            return False
    
    def add_user(self, telegram_id: int) -> int:
        """Add new user and return user ID"""
        # Check if user already exists
        for user in self.data["users"]:
            if user["telegram_id"] == telegram_id:
                return user["id"]
        
        # Create new user
        self.data["counters"]["user_id"] += 1
        user_id = self.data["counters"]["user_id"]
        
        new_user = {
            "id": user_id,
            "telegram_id": telegram_id
        }
        
        self.data["users"].append(new_user)
        self._save_database()
        return user_id
    
    def get_user_id(self, telegram_id: int) -> Optional[int]:
        """Get user ID by telegram ID"""
        for user in self.data["users"]:
            if user["telegram_id"] == telegram_id:
                return user["id"]
        return None
    
    def add_news(self, content: str, keywords: List[str], author_id: int) -> int:
        """Add new news article and return news ID"""
        self.data["counters"]["news_id"] += 1
        news_id = self.data["counters"]["news_id"]
        
        new_news = {
            "id": news_id,
            "time_added": datetime.now(timezone.utc).isoformat(),
            "content": content,
            "keywords": keywords,
            "author": author_id
        }
        
        self.data["news"].append(new_news)
        self._save_database()
        return news_id
    
    def add_like(self, user_id: int, news_id: int) -> bool:
        """Add like to news article"""
        # Check if like already exists
        for like in self.data["likes"]:
            if like["user_id"] == user_id and like["news_id"] == news_id:
                return False  # Already liked
        
        self.data["counters"]["like_id"] += 1
        like_id = self.data["counters"]["like_id"]
        
        new_like = {
            "id": like_id,
            "user_id": user_id,
            "news_id": news_id
        }
        
        self.data["likes"].append(new_like)
        self._save_database()
        return True
    
    def get_news_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Get news articles that contain any of the specified keywords"""
        matching_news = []
        keywords_lower = [kw.lower() for kw in keywords]
        
        for news in self.data["news"]:
            news_keywords_lower = [kw.lower() for kw in news["keywords"]]
            news_content_lower = news["content"].lower()
            
            # Check if any keyword matches
            for keyword in keywords_lower:
                if (keyword in news_keywords_lower or 
                    keyword in news_content_lower):
                    matching_news.append(news)
                    break
        
        return matching_news
    
    def get_news_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get news articles added within date range"""
        matching_news = []
        
        for news in self.data["news"]:
            news_date = datetime.fromisoformat(news["time_added"].replace('Z', '+00:00'))
            if start_date <= news_date <= end_date:
                matching_news.append(news)
        
        return matching_news
    
    def get_news_by_id(self, news_id: int) -> Optional[Dict[str, Any]]:
        """Get news article by ID"""
        for news in self.data["news"]:
            if news["id"] == news_id:
                return news
        return None
    
    def get_likes_count(self, news_id: int) -> int:
        """Get number of likes for a news article"""
        count = 0
        for like in self.data["likes"]:
            if like["news_id"] == news_id:
                count += 1
        return count

class NewsBot:
    """Main bot class handling all Telegram interactions"""
    
    def __init__(self, token: str):
        self.db = NewsBotDatabase()
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("add_news", self.add_news_command))
        self.application.add_handler(CommandHandler("like_news", self.like_news_command))
        self.application.add_handler(CommandHandler("get_news", self.get_news_command))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        self.db.add_user(user_id)
        
        welcome_message = """
🤖 Welcome to News Bot!

This bot helps you manage and share news articles. Here are the available commands:

/add_news - Add a new news article with keywords
/like_news - Like a news article by ID
/get_news - Search news by keywords
/help - Show this help message

Type /help for more detailed information about each command.
        """
        
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 News Bot Commands:

/add_news - Add a new news article
Usage: /add_news
The bot will ask you for:
1. News content
2. Keywords (comma-separated)

/like_news - Like a news article
Usage: /like_news <news_id>
Example: /like_news 123

/get_news - Search news by keywords
Usage: /get_news <keywords>
Example: /get_news technology, AI, python

The bot automatically sends a daily digest of all news at 7:30 AM Moscow time.
        """
        
        await update.message.reply_text(help_text)
    
    async def add_news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add_news command"""
        user_id = update.effective_user.id
        db_user_id = self.db.add_user(user_id)
        
        # Store user state for multi-step input
        context.user_data['waiting_for_news_content'] = True
        context.user_data['db_user_id'] = db_user_id
        
        await update.message.reply_text(
            "📰 Please send me the news content you want to add:"
        )
    
    async def like_news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /like_news command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a news ID.\nUsage: /like_news <news_id>"
            )
            return
        
        try:
            news_id = int(context.args[0])
            user_id = update.effective_user.id
            db_user_id = self.db.add_user(user_id)
            
            # Check if news exists
            news = self.db.get_news_by_id(news_id)
            if not news:
                await update.message.reply_text(f"❌ News with ID {news_id} not found.")
                return
            
            # Add like
            if self.db.add_like(db_user_id, news_id):
                likes_count = self.db.get_likes_count(news_id)
                await update.message.reply_text(
                    f"👍 You liked news #{news_id}!\n"
                    f"Total likes: {likes_count}"
                )
            else:
                await update.message.reply_text(f"ℹ️ You have already liked news #{news_id}.")
                
        except ValueError:
            await update.message.reply_text("❌ Please provide a valid news ID (number).")
        except Exception as e:
            logger.error(f"Error in like_news_command: {e}")
            await update.message.reply_text("❌ An error occurred while processing your request.")
    
    async def get_news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /get_news command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide keywords to search.\nUsage: /get_news <keywords>"
            )
            return
        
        # Join all arguments as keywords
        keywords_text = ' '.join(context.args)
        keywords = [kw.strip() for kw in keywords_text.split(',')]
        
        try:
            matching_news = self.db.get_news_by_keywords(keywords)
            
            if not matching_news:
                await update.message.reply_text(
                    f"🔍 No news found matching keywords: {', '.join(keywords)}"
                )
                return
            
            # Send news articles
            message = f"📰 Found {len(matching_news)} news article(s) matching: {', '.join(keywords)}\n\n"
            
            for news in matching_news[:10]:  # Limit to 10 articles
                likes_count = self.db.get_likes_count(news["id"])
                news_date = datetime.fromisoformat(news["time_added"].replace('Z', '+00:00'))
                formatted_date = news_date.strftime("%Y-%m-%d %H:%M")
                
                message += f"📄 News #{news['id']}\n"
                message += f"📅 {formatted_date}\n"
                message += f"👍 {likes_count} likes\n"
                message += f"🏷️ Keywords: {', '.join(news['keywords'])}\n"
                message += f"📝 Content: {news['content'][:200]}{'...' if len(news['content']) > 200 else ''}\n\n"
            
            if len(matching_news) > 10:
                message += f"... and {len(matching_news) - 10} more articles."
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in get_news_command: {e}")
            await update.message.reply_text("❌ An error occurred while searching for news.")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_data = context.user_data
        
        if user_data.get('waiting_for_news_content'):
            # User is providing news content
            news_content = update.message.text
            user_data['news_content'] = news_content
            user_data['waiting_for_news_content'] = False
            user_data['waiting_for_keywords'] = True
            
            await update.message.reply_text(
                "🏷️ Great! Now please send me the keywords for this news (comma-separated):"
            )
        
        elif user_data.get('waiting_for_keywords'):
            # User is providing keywords
            keywords_text = update.message.text
            keywords = [kw.strip() for kw in keywords_text.split(',')]
            
            try:
                news_id = self.db.add_news(
                    user_data['news_content'],
                    keywords,
                    user_data['db_user_id']
                )
                
                # Clear user data
                user_data.clear()
                
                await update.message.reply_text(
                    f"✅ News added successfully!\n"
                    f"📰 News ID: {news_id}\n"
                    f"🏷️ Keywords: {', '.join(keywords)}"
                )
                
            except Exception as e:
                logger.error(f"Error adding news: {e}")
                user_data.clear()
                await update.message.reply_text("❌ An error occurred while adding the news.")
        
        else:
            # Regular text message
            await update.message.reply_text(
                "🤖 I didn't understand that. Use /help to see available commands."
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
    
    async def send_daily_digest(self):
        """Send daily news digest to all users"""
        try:
            # Calculate date range for yesterday's news
            now = datetime.now(MOSCOW_TIMEZONE)
            yesterday_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_end = yesterday_start.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Convert to UTC for database comparison
            yesterday_start_utc = yesterday_start.astimezone(timezone.utc)
            yesterday_end_utc = yesterday_end.astimezone(timezone.utc)
            
            # Get yesterday's news
            yesterday_news = self.db.get_news_by_date_range(yesterday_start_utc, yesterday_end_utc)
            
            if not yesterday_news:
                logger.info("No news to send in daily digest")
                return
            
            # Prepare digest message
            digest_message = f"📰 Daily News Digest - {yesterday_start.strftime('%Y-%m-%d')}\n\n"
            digest_message += f"Found {len(yesterday_news)} news article(s) from yesterday:\n\n"
            
            for news in yesterday_news:
                likes_count = self.db.get_likes_count(news["id"])
                news_date = datetime.fromisoformat(news["time_added"].replace('Z', '+00:00'))
                formatted_date = news_date.astimezone(MOSCOW_TIMEZONE).strftime("%H:%M")
                
                digest_message += f"📄 News #{news['id']} ({formatted_date})\n"
                digest_message += f"👍 {likes_count} likes\n"
                digest_message += f"🏷️ Keywords: {', '.join(news['keywords'])}\n"
                digest_message += f"📝 {news['content'][:150]}{'...' if len(news['content']) > 150 else ''}\n\n"
            
            # Send to all users
            sent_count = 0
            for user in self.db.data["users"]:
                try:
                    await self.application.bot.send_message(
                        chat_id=user["telegram_id"],
                        text=digest_message
                    )
                    sent_count += 1
                except TelegramError as e:
                    logger.warning(f"Failed to send digest to user {user['telegram_id']}: {e}")
            
            logger.info(f"Daily digest sent to {sent_count} users")
            
        except Exception as e:
            logger.error(f"Error sending daily digest: {e}")
    
    def schedule_daily_digest(self):
        """Schedule daily news digest"""
        async def daily_job():
            while True:
                try:
                    # Calculate next 7:30 AM Moscow time
                    now = datetime.now(MOSCOW_TIMEZONE)
                    target_time = now.replace(hour=7, minute=30, second=0, microsecond=0)
                    
                    # If it's already past 7:30 today, schedule for tomorrow
                    if now >= target_time:
                        target_time += timedelta(days=1)
                    
                    # Calculate seconds until target time
                    wait_seconds = (target_time - now).total_seconds()
                    
                    logger.info(f"Next daily digest scheduled for {target_time}")
                    await asyncio.sleep(wait_seconds)
                    
                    await self.send_daily_digest()
                    
                except Exception as e:
                    logger.error(f"Error in daily job: {e}")
                    await asyncio.sleep(3600)  # Wait 1 hour before retrying
        
        # Start the daily job
        asyncio.create_task(daily_job())
    
    def run(self):
        """Start the bot"""
        logger.info("Starting News Bot...")
        
        # Schedule daily digest
        self.schedule_daily_digest()
        
        # Start the bot
        self.application.run_polling()

def main():
    """Main function to run the bot"""
    # Get bot token from environment variable
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        logger.error("Please create a .env file with your bot token or set the environment variable.")
        return
    
    try:
        # Create and run the bot
        bot = NewsBot(bot_token)
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    main()
