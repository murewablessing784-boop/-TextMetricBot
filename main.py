import os
import sys
import logging
import re
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

# --- Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Config ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_TOKEN environment variable not set!")
    sys.exit(1)

# --- Analysis Functions ---
def analyze_text(text: str) -> dict:
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    
    sentences = re.split(r'[.!?]+', text)
    sentence_count = len([s for s in sentences if s.strip()])
    
    unique_words = set(word.lower() for word in words)
    unique_count = len(unique_words)
    
    word_freq = Counter(word.lower() for word in words)
    repeated_words = {word: count for word, count in word_freq.items() if count > 1}
    
    nouns = []
    verbs = []
    adjectives = []
    adverbs = []
    
    for word in words:
        clean_word = re.sub(r'[^\w\s]', '', word)
        if not clean_word:
            continue
        if clean_word[0].isupper() and len(clean_word) > 1:
            nouns.append(clean_word)
        elif clean_word.endswith(('ing', 'ed', 'es')) and len(clean_word) > 3:
            verbs.append(clean_word)
        elif clean_word.endswith(('ous', 'ful', 'ive', 'able', 'ible')):
            adjectives.append(clean_word)
        elif clean_word.endswith('ly'):
            adverbs.append(clean_word)
    
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
    result = (
        f"📊 Text Analysis Results\n"
        f"─────────────────────────────\n"
        f"📝 Words: {analysis['word_count']}\n"
        f"🔤 Characters: {analysis['char_count']}\n"
        f"📄 Sentences: {analysis['sentence_count']}\n"
        f"✨ Unique Words: {analysis['unique_count']}\n"
    )
    
    if analysis['repeated_words']:
        repeated_list = sorted(analysis['repeated_words'].items(), key=lambda x: x[1], reverse=True)[:5]
        result += f"\n♾️ Repeated Words:\n"
        for word, count in repeated_list:
            result += f"   • {word}: {count}x\n"
        if len(analysis['repeated_words']) > 5:
            result += f"   ...and {len(analysis['repeated_words'])-5} more\n"
    
    if analysis['nouns']:
        result += f"\n👑 Nouns: {', '.join(analysis['nouns'][:5])}"
        if len(analysis['nouns']) > 5:
            result += f" +{len(analysis['nouns'])-5} more"
    
    if analysis['verbs']:
        result += f"\n🏃 Verbs: {', '.join(analysis['verbs'][:5])}"
        if len(analysis['verbs']) > 5:
            result += f" +{len(analysis['verbs'])-5} more"
    
    if analysis['adjectives']:
        result += f"\n☁️ Adjectives: {', '.join(analysis['adjectives'][:5])}"
        if len(analysis['adjectives']) > 5:
            result += f" +{len(analysis['adjectives'])-5} more"
    
    if analysis['adverbs']:
        result += f"\n💨 Adverbs: {', '.join(analysis['adverbs'][:5])}"
        if len(analysis['adverbs']) > 5:
            result += f" +{len(analysis['adverbs'])-5} more"
    
    return result

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("📊 Full Analysis", callback_data="full_analysis"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📊 Welcome to TextMetricBot, {user.first_name}!\n\n"
        "I analyze text and provide detailed metrics.\n\n"
        "🔍 What I can do:\n"
        "• Count words and characters\n"
        "• Count sentences\n"
        "• Find repeated words\n"
        "• Identify parts of speech\n\n"
        "💡 How to use:\n"
        "• Send me any text for analysis\n"
        "• Use /help for all commands\n\n"
        "📝 Try sending a message now!",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 TextMetricBot Commands\n\n"
        "Main Commands:\n"
        "• /start - Show main menu\n"
        "• /help - Show this help\n"
        "• /full_analysis - Full breakdown\n\n"
        "Quick Metrics:\n"
        "• /word_count - Total words\n"
        "• /char_count - Total characters\n"
        "• /sentence_count - Total sentences\n"
        "• /unique_words - Unique words\n"
        "• /repeated_words - Repeated words\n\n"
        "Parts of Speech:\n"
        "• /nouns - Extract nouns\n"
        "• /verbs - Extract verbs\n"
        "• /adjectives - Extract adjectives\n"
        "• /adverbs - Extract adverbs\n\n"
        "💡 Tip: Send any text for instant analysis!"
    )

async def full_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text(
            "📝 Please send me some text first!\n"
            "💡 Send any message and I'll analyze it."
        )
        return
    
    analysis = analyze_text(text)
    result = format_analysis(analysis)
    result += f"\n\n📝 Original Text:\n{analysis['text_preview']}"
    
    await update.message.reply_text(result)

async def word_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("📝 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    await update.message.reply_text(
        f"📝 Word Count: {analysis['word_count']}\n\n"
        f"Preview: {analysis['text_preview']}"
    )

async def char_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("🔤 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    await update.message.reply_text(
        f"🔤 Character Count: {analysis['char_count']}\n\n"
        f"Preview: {analysis['text_preview']}"
    )

async def sentence_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("📄 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    await update.message.reply_text(
        f"📄 Sentence Count: {analysis['sentence_count']}\n\n"
        f"Preview: {analysis['text_preview']}"
    )

async def unique_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("✨ Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    await update.message.reply_text(
        f"✨ Unique Words: {analysis['unique_count']}\n\n"
        f"Preview: {analysis['text_preview']}"
    )

async def repeated_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("♾️ Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['repeated_words']:
        await update.message.reply_text("♾️ No repeated words found!")
        return
    
    result = "♾️ Repeated Words:\n"
    sorted_words = sorted(analysis['repeated_words'].items(), key=lambda x: x[1], reverse=True)
    for word, count in sorted_words[:15]:
        result += f"• {word}: {count}x\n"
    if len(sorted_words) > 15:
        result += f"\n...and {len(sorted_words)-15} more"
    
    await update.message.reply_text(result)

async def nouns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("👑 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['nouns']:
        await update.message.reply_text("👑 No nouns found!")
        return
    
    await update.message.reply_text(
        f"👑 Nouns Found ({len(analysis['nouns'])}):\n{', '.join(analysis['nouns'])}"
    )

async def verbs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("🏃 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['verbs']:
        await update.message.reply_text("🏃 No verbs found!")
        return
    
    await update.message.reply_text(
        f"🏃 Verbs Found ({len(analysis['verbs'])}):\n{', '.join(analysis['verbs'])}"
    )

async def adjectives(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("☁️ Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['adjectives']:
        await update.message.reply_text("☁️ No adjectives found!")
        return
    
    await update.message.reply_text(
        f"☁️ Adjectives Found ({len(analysis['adjectives'])}):\n{', '.join(analysis['adjectives'])}"
    )

async def adverbs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = context.user_data.get('last_text')
    if not text:
        await update.message.reply_text("💨 Please send me some text first!")
        return
    
    analysis = analyze_text(text)
    if not analysis['adverbs']:
        await update.message.reply_text("💨 No adverbs found!")
        return
    
    await update.message.reply_text(
        f"💨 Adverbs Found ({len(analysis['adverbs'])}):\n{', '.join(analysis['adverbs'])}"
    )

# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['last_text'] = text
    
    analysis = analyze_text(text)
    
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
    
    await update.message.reply_text(
        f"📊 Quick Analysis\n"
        f"─────────────────────\n"
        f"📝 Words: {analysis['word_count']}\n"
        f"🔤 Characters: {analysis['char_count']}\n"
        f"📄 Sentences: {analysis['sentence_count']}\n"
        f"✨ Unique Words: {analysis['unique_count']}\n"
        f"♾️ Repeated Words: {len(analysis['repeated_words'])}\n\n"
        f"💡 Use /full_analysis for detailed breakdown",
        reply_markup=reply_markup
    )

# --- Callback Handler ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        result += f"\n\n📝 Original:\n{analysis['text_preview']}"
        await query.edit_message_text(result)
    
    elif data == "repeated_words":
        if not analysis['repeated_words']:
            await query.edit_message_text("♾️ No repeated words found!")
            return
        result = "♾️ Repeated Words:\n"
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
            f"👑 Nouns ({len(analysis['nouns'])}):\n{', '.join(analysis['nouns'])}"
        )
    
    elif data == "verbs":
        if not analysis['verbs']:
            await query.edit_message_text("🏃 No verbs found!")
            return
        await query.edit_message_text(
            f"🏃 Verbs ({len(analysis['verbs'])}):\n{', '.join(analysis['verbs'])}"
        )
    
    elif data == "help":
        await help_command(update, context)

# --- Error Handler ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

# --- Main ---
def main():
    try:
        logger.info("🚀 Starting TextMetricBot...")
        
        app = Application.builder().token(TOKEN).build()
        
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
        
        logger.info("✅ Bot is running!")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
