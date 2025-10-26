# Telegram News Bot

A Telegram bot for managing news articles with features like adding news with keywords, daily news digest, liking news articles, and searching news by keywords.

## Features

- **Add News**: Add news articles with keywords using `/add_news` command
- **Daily Digest**: Automatically sends daily news digest at 7:30 AM Moscow time
- **Like News**: Like news articles by ID using `/like_news` command
- **Search News**: Search news by keywords using `/get_news` command
- **JSON Database**: All data is stored in a JSON file for simplicity
- **Error Handling**: Comprehensive error handling throughout the bot

## Installation

1. **Clone or download the project files**
   ```bash
   # If you have git
   git clone <repository-url>
   cd telegram_news_bot
   
   # Or simply download the files to a folder
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a Telegram Bot**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Follow the instructions to create your bot
   - Save the bot token you receive

4. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env file and add your bot token
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

## Usage

1. **Start the bot**
   ```bash
   python bot.py
   ```

2. **Available Commands**
   - `/start` - Start the bot and get welcome message
   - `/help` - Show help information
   - `/add_news` - Add a new news article (interactive)
   - `/like_news <news_id>` - Like a news article by ID
   - `/get_news <keywords>` - Search news by keywords

## Bot Commands Details

### `/add_news`
Interactive command to add news:
1. Bot asks for news content
2. Bot asks for keywords (comma-separated)
3. News is added to database with unique ID

### `/like_news <news_id>`
Like a news article:
- Example: `/like_news 123`
- Shows total likes count
- Prevents duplicate likes from same user

### `/get_news <keywords>`
Search news by keywords:
- Example: `/get_news technology, AI, python`
- Searches both content and keywords
- Shows up to 10 results with details

## Database Structure

The bot uses a JSON file (`news_bot_database.json`) to store:

- **Users**: ID, Telegram ID
- **News**: ID, timestamp, content, keywords, author ID
- **Likes**: ID, User ID, News ID

## Daily Digest

The bot automatically sends a daily digest at 7:30 AM Moscow time containing:
- All news added in the previous day
- News IDs, timestamps, like counts
- Keywords and content previews

## Configuration

### Environment Variables
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (required)

### Database File
- `news_bot_database.json` - Automatically created on first run

## Error Handling

The bot includes comprehensive error handling for:
- Invalid commands and arguments
- Database file operations
- Telegram API errors
- Network connectivity issues
- User input validation

## Logging

The bot logs all activities including:
- Bot startup and shutdown
- Command executions
- Database operations
- Daily digest scheduling
- Error conditions

## Requirements

- Python 3.7+
- python-telegram-bot 20.7+
- pytz 2023.3+
- python-dotenv 1.0.0+

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if bot token is correct
   - Verify bot is running without errors
   - Check internet connection

2. **Database errors**
   - Ensure write permissions in bot directory
   - Check if `news_bot_database.json` is corrupted

3. **Daily digest not sending**
   - Check bot is running continuously
   - Verify timezone settings
   - Check logs for errors

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify your bot token is correct
3. Ensure all dependencies are installed
4. Check file permissions

## License

This project is open source and available under the MIT License.
