import os
import sys
import logging
import re
from datetime import datetime
from collections import Counter

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# --- Logging Configuration ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("❌ TELEGRAM_TOKEN environment variable not set!")
    sys.exit(1)

# --- Text Analysis Functions ---
def analyze_text(text: str) -> dict:
    """Analyze text and return various metrics."""
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    
    # Count sentences (split by ., !, ?)
    sentences = re.split(r'[.!?]+', text)
    sentence_count = len([s for s in sentences if s.strip()])
    
    # Unique words
    unique_words = set(word.lower() for word in words)
    unique_count = len(unique_words)
    
    # Repeated words
    word_freq = Counter(word.lower() for word in words)
    repeated_words = {word: count for word, count in word_freq.items() if count > 1}
    
    # Simple part-of-speech extraction
    nouns = []
    verbs = []
    adjectives = []
    adverbs = []
    
    for word in words:
        # Nouns: capitalized words or after 'the', 'a', 'an'
        if word[0].isupper() or word.lower() in ['the', 'a', 'an']:
            if len(word) > 1 and word[0].isalpha():
                nouns.append(word)
        # Verbs: ending in 'ing', 'ed', 'es'
        elif word.endswith(('ing', 'ed', 'es')) and len(word) > 3:
            verbs.append(word)
        # Adjectives: ending in 'ous', 'ful', 'ive', 'able', 'ible'
        elif word.endswith(('ous', 'ful', 'ive', 'able', 'ible')):
            adjectives.append(word)
        # Adverbs: ending in 'ly'
        elif word.endswith('ly'):
            adverbs.append(word)
    
    return {
        'word_count': word_count,
        'char_count': char_count,
        'sentence_count': sentence_count,
        'unique_count': unique_count,
        'repeated_words': repeated_words,
        'nouns': list(set(nouns))[:10],
        'verbs': list(set(verbs))[:10],
        'adjectives': list(set(adjectives))[:10],
        'adverbs': list(set(adverbs))[:10],
        'text_preview': text[:200] + ('...' if len(text) > 200 else '')
    }

def format_analysis(analysis: dict) -> str:
    """Format analysis results for display."""
    result = (
        f"📊 **Text Analysis Results**\n"
        f"─────────────────────────────\n"
        f"📝 Words: {analysis['word_count']}\n"
        f"🔤 Characters: {analysis['char_count']}\n"
        f"📄 Sentences: {analysis['sentence_count']}\n"
        f"✨ Unique Words: {analysis['unique_count']}\n"
    )
    
    # Add repeated words
    if analysis['repeated_words']:
        repeated_list = sorted(analysis['repeated_words'].items(), key=lambda x: x[1], reverse=True)[:5]
        result += f"\n♾️ **Repeated Words:**\n"
        for word, count in repeated_list:
            result += f"   • {word}: {count}x\n"
        if len(analysis['repeated_words']) > 5:
            result += f"   ...and {len(analysis['repeated_words'])-5} more\n"
    
    # Add parts of speech
    if analysis['nouns']:
        result += f"\n👑 **Nouns:** {', '.join(analysis['nouns'][:5])}"
        if len(analysis['nouns']) > 5:
            result += f" +{len(analysis['nouns'])-5} more"
    
    if analysis['verbs']:
        result += f"\n🏃 **Verbs:** {', '.join(analysis['verbs'][:5])}"
        if len(analysis['verbs']) > 5:
            result += f" +{len(analysis['verbs'])-5} more"
    
    if analysis['adjectives']:
        result += f"\n☁️ **Adjectives:** {', '.join(analysis['adjectives'][:5])}"
        if len(analysis['adjectives']) > 5:
            result += f" +{len(analysis['adjectives'])-5} more"
    
    if analysis['adverbs']:
        result += f"\n💨 **Adverbs:** {', '.join(analysis['adverbs'][:5])}"
        if len(analysis['adverbs']) > 5:
            result += f" +{len(analysis['adverbs'])-5} more"
    
    return result

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    welcome = (
        f"📊 **Welcome to TextMetricBot, {user.first_name}!**\n\n"
        "I analyze text and provide detailed metrics.\n\n"
        "🔍 **What I can do:**\n"
        "• Count words and characters\n"
        "• Count sentences\n"
        "• Find repeated words\n"
        "• Identify nouns, verbs, adjectives, adverbs\n\n"
        "💡 **How to use:**\n"
        "• Send me any text for instant analysis\n"
        "• Use /full_analysis for detailed breakdown\n"
        "• Use /help for all commands\n\n"
        "📝 Try sending a message now!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Full Analysis", callback_data="full_analysis"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = (
        "📖 **TextMetricBot Commands**\n\n"
        "**Main Commands:**\n"
        "• `/start` - Show main menu\n"
        "• `/help` - Show this help\n"
        "• `/full_analysis` - Full text breakdown\n\n"
        "**Quick Metrics:**\n"
        "• `/word_count` - Total words\n"
        "• `/char_count` - Total characters\n"
        "• `/sentence_count` - Total sentences\n"
        "• `/unique_words` - Unique words\n"
        "• `/repeated_words` - Repeated words\n\n"
        "**Parts of Speech:**\n"
        "• `/nouns` - Extract nouns\n"
        "• `/verbs` - Extract verbs\n"
        "• `/adjectives` - Extract adjectives\n"
        "• `/adverbs` - Extract adverbs\n\n"
        "💡 **Tip:** Send any text message for instant analysis!"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def full_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /full_analysis command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text(
            "📝 Please send me some text first, then use this command.\n"
            "💡 Send any message and I'll analyze it!"
        )
        return
    
    analysis = analyze_text(text)
    result = format_analysis(analysis)
    result += f"\n\n📝 **Original Text:**\n_{analysis['text_preview']}_"
    
    await update.message.reply_text(result, parse_mode='Markdown')

async def word_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /word_count command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("📝 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    await update.message.reply_text(
        f"📝 **Word Count:** {analysis['word_count']}\n\n"
        f"Preview: _{analysis['text_preview']}_",
        parse_mode='Markdown'
    )

async def char_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /char_count command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("🔤 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    await update.message.reply_text(
        f"🔤 **Character Count:** {analysis['char_count']}\n\n"
        f"Preview: _{analysis['text_preview']}_",
        parse_mode='Markdown'
    )

async def sentence_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sentence_count command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("📄 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    await update.message.reply_text(
        f"📄 **Sentence Count:** {analysis['sentence_count']}\n\n"
        f"Preview: _{analysis['text_preview']}_",
        parse_mode='Markdown'
    )

async def unique_words(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unique_words command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("✨ Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    await update.message.reply_text(
        f"✨ **Unique Words:** {analysis['unique_count']}\n\n"
        f"Preview: _{analysis['text_preview']}_",
        parse_mode='Markdown'
    )

async def repeated_words(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /repeated_words command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("♾️ Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['repeated_words']:
        await update.message.reply_text("♾️ No repeated words found!")
        return
    
    result = "♾️ **Repeated Words:**\n"
    sorted_words = sorted(analysis['repeated_words'].items(), key=lambda x: x[1], reverse=True)
    for word, count in sorted_words[:15]:
        result += f"• {word}: {count}x\n"
    if len(sorted_words) > 15:
        result += f"\n...and {len(sorted_words)-15} more"
    
    await update.message.reply_text(result)

async def nouns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /nouns command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("👑 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['nouns']:
        await update.message.reply_text("👑 No nouns found!")
        return
    
    await update.message.reply_text(
        f"👑 **Nouns Found ({len(analysis['nouns'])}):**\n{', '.join(analysis['nouns'])}"
    )

async def verbs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /verbs command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("🏃 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['verbs']:
        await update.message.reply_text("🏃 No verbs found!")
        return
    
    await update.message.reply_text(
        f"🏃 **Verbs Found ({len(analysis['verbs'])}):**\n{', '.join(analysis['verbs'])}"
    )

async def adjectives(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /adjectives command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("☁️ Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['adjectives']:
        await update.message.reply_text("☁️ No adjectives found!")
        return
    
    await update.message.reply_text(
        f"☁️ **Adjectives Found ({len(analysis['adjectives'])}):**\n{', '.join(analysis['adjectives'])}"
    )

async def adverbs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /adverbs command."""
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("💨 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['adverbs']:
        await update.message.reply_text("💨 No adverbs found!")
        return
    
    await update.message.reply_text(
        f"💨 **Adverbs Found ({len(analysis['adverbs'])}):**\n{', '.join(analysis['adverbs'])}"
    )

# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any non-command messages."""
    text = update.message.text
    
    # Store for later commands
    context.user_data['last_text'] = text
    
    # Analyze
    analysis = analyze_text(text)
    
    # Show typing
    await update.message.chat.send_action(action="typing")
    
    # Quick summary
    summary = (
        f"📊 **Quick Analysis**\n"
        f"─────────────────────\n"
        f"📝 Words: {analysis['word_count']}\n"
        f"🔤 Characters: {analysis['char_count']}\n"
        f"📄 Sentences: {analysis['sentence_count']}\n"
        f"✨ Unique Words: {analysis['unique_count']}\n"
        f"♾️ Repeated Words: {len(analysis['repeated_words'])}\n\n"
        f"💡 Use /full_analysis for detailed breakdown"
    )
    
    # Buttons
    keyboard = [
        [
            InlineKeyboardButton("📊 Full Analysis", callback_data="full_analysis"),
            InlineKeyboardButton("♾️ Repeated", callback_data="repeated_words"),
        ],
        [
            InlineKeyboardButton("👑 Nouns", callback_data="nouns"),
            InlineKeyboardButton("🏃 Verbs", callback_data="verbs"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='Markdown')

# --- Callback Handler ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    text = context.user_data.get('last_text')
    
    if not text:
        await query.edit_message_text("📝 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    
    if data == "full_analysis":
        result = format_analysis(analysis)
        result += f"\n\n📝 **Original:**\n_{analysis['text_preview']}_"
        await query.edit_message_text(result, parse_mode='Markdown')
    
    elif data == "repeated_words":
        if not analysis['repeated_words']:
            await query.edit_message_text("♾️ No repeated words found!")
            return
        result = "♾️ **Repeated Words:**\n"
        sorted_words = sorted(analysis['repeated_words'].items(), key=lambda x: x[1], reverse=True)
        for word, count in sorted_words[:15]:
            result += f"• {word}: {count}x\n"
        if len(sorted_words) > 15:
            result += f"\n...and {len(sorted_words)-15} more"
        await query.edit_message_text(result)
    
    elif data == "nouns":
        if not analysis['nouns']:
            await query.edit_message_text("👑 No nouns found!")
            return
        await query.edit_message_text(
            f"👑 **Nouns ({len(analysis['nouns'])}):**\n{', '.join(analysis['nouns'])}"
        )
    
    elif data == "verbs":
        if not analysis['verbs']:
            await query.edit_message_text("🏃 No verbs found!")
            return
        await query.edit_message_text(
            f"🏃 **Verbs ({len(analysis['verbs'])}):**\n{', '.join(analysis['verbs'])}"
        )
    
    elif data == "help":
        await help_command(update, context)
    
    else:
        await query.edit_message_text("❌ Unknown command.")

# --- Error Handler ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

# --- Main Function ---
def main() -> None:
    """Start the bot."""
    try:
        logger.info("🚀 Starting TextMetricBot...")
        logger.info(f"🤖 Bot Token: {TOKEN[:10]}... (truncated)")
        
        # Create application
        app = Application.builder().token(TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("full_analysis", full_analysis))
        app.add_handler(CommandHandler("word_count", word_count))
        app.add_handler(CommandHandler("char_count", char_count))
        app.add_handler(CommandHandler("sentence_count", sentence_count))
        app.add_handler(CommandHandler("unique_words", unique_words))
        app.add_handler(CommandHandler("repeated_words", repeated_words))
        app.add_handler(CommandHandler("nouns", nouns))
        app.add_handler(CommandHandler("verbs", verbs))
        app.add_handler(CommandHandler("adjectives", adjectives))
        app.add_handler(CommandHandler("adverbs", adverbs))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_error_handler(error_handler)
        
        # Start
        logger.info("✅ Bot is running and ready for messages!")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
