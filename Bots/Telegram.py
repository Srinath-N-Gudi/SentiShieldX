import asyncio
import logging
from dotenv import load_dotenv
import os 
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from textblob import TextBlob  # For sentiment analysis
from detoxify import Detoxify

hate_speech_detector = Detoxify("multilingual")

# Loading Local Enviroment Variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM-BOT-TOKEN')

# Logging System
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)



def analyze_sentiment(text: str) -> str:
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity

    if polarity > 0:
        return "positive"
    elif polarity < 0:
        return "negative"
    else:
        return "neutral"

# Function to detect cyberbullying using a pre-trained model
def detect_hate_speech(text: str) -> bool:
    results = hate_speech_detector.predict(text)
    # Check if any of the toxicity scores exceed a threshold (e.g., 0.8)
    if any(score > 0.8 for score in results.values()):
        return True
    return False


async def handle_message(update: Update, context):
    user = update.message.from_user
    message_text = update.message.text

    # Print the message and user info
    print(f"Received message from {user.first_name} ({user.username}): {message_text}")

    # Perform sentiment analysis
    sentiment = analyze_sentiment(message_text)
    print(f"Sentiment: {sentiment}")

    # Detect cyberbullying
    is_cyberbullying = detect_hate_speech(message_text)
    print(f"Cyberbullying detected: {is_cyberbullying}")

    # Generate a reply based on sentiment and cyberbullying detection
    reply = generate_reply(user.first_name, message_text, sentiment, is_cyberbullying)

    # Send the reply
    await update.message.reply_text(reply)

# Function to generate replies based on the message content

def generate_reply(user_name: str, message_text: str, sentiment: str, is_cyberbullying: bool) -> str:
    if is_cyberbullying:
        return f"⚠️ {user_name}, your message was flagged as potentially harmful. Please be kind and respectful."
    elif sentiment == "positive":
        return f"😊 That's great to hear, {user_name}! Keep spreading positivity!"
    elif sentiment == "negative":
        return f"😢 I'm sorry you're feeling this way, {user_name}. Let me know if I can help."
    else:
        return f"🤔 Interesting, {user_name}! You said: {message_text}"

# Main function to set up the bot
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Starting the Bot
    application.run_polling()

if __name__ == "__main__":
    main()