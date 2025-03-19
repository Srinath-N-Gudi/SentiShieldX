from flask import render_template, request, redirect, url_for
from app import app

# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


import discord
from discord.ext import commands

@app.route('/add_bot', methods=['POST'])
def add_bot():
    bot_name = request.form['bot_name']
    community_type = request.form['community_type']

    if community_type == 'discord':
        bot = commands.Bot(command_prefix='!')

        @bot.event
        async def on_message(message):
            if "cyberbullying" in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, cyberbullying is not allowed here.")

        bot.run('YOUR_DISCORD_BOT_TOKEN')
        return redirect(url_for('dashboard'))
    
    from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from flask import render_template, request, redirect, url_for
from app import app
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import threading

# Global variable to store the Telegram bot updater
telegram_updater = None

@app.route('/add_bot', methods=['POST'])
def add_bot():
    global telegram_updater

    bot_name = request.form['bot_name']
    community_type = request.form['community_type']

    if community_type == 'telegram':
        # Initialize the Telegram bot
        telegram_updater = Updater("YOUR_TELEGRAM_BOT_TOKEN", use_context=True)

        # Define the message handler
        def handle_message(update: Update, context: CallbackContext):
            if "cyberbullying" in update.message.text.lower():
                # Delete the message containing cyberbullying
                update.message.delete()
                # Send a warning message to the user
                update.message.reply_text(f"{update.message.from_user.username}, cyberbullying is not allowed here.")

        # Add the message handler to the dispatcher
        telegram_updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

        # Start the bot in a separate thread to avoid blocking the Flask app
        threading.Thread(target=telegram_updater.start_polling).start()

        return redirect(url_for('dashboard'))