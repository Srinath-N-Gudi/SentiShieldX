import discord
import os
from dotenv import load_dotenv
from textblob import TextBlob  # For sentiment analysis
from detoxify import Detoxify
import logging

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True  # Enable message reading permissions

hate_speech_detector = Detoxify("multilingual")

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore messages from itself



    msg = message.content.lower() 
    # Analyze Sentiment and try detecting hate speech using the functions
    sentiment = analyze_sentiment(msg)
    is_cyberbullying = detect_hate_speech(msg)

    # If the message contains the word "cyberbullying" or the sentiment is negative, send a warning
    if is_cyberbullying or sentiment == "negative":
        await message.channel.send("Warning: Your message contains explicit or offensive language. Please be respectful.")
    
    print("SENTIMENT : ", sentiment)
    print("IS CYBERBULLYING : ", is_cyberbullying)
    
    if msg == "hello":
        await message.channel.send("Hello! I am your bot.")


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



# Run the bot
bot.run(TOKEN)
