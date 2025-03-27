# APP/run.py
from init import app
from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, current_user, login_required
import secrets
import logging
from Database.db import db, User
from features.ytca import CommentAnalyzer
from features.Cyber import Cyber
from features.bots.telegram import TelegramBot
from features.bots.bot_resp import response_generator
import os
from dotenv import load_dotenv
import io
import sys
from Database.telegram_database import TelegramDatabase
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')



# Initialize logging    
logging.basicConfig(
    level=logging.ERROR,
    format='[%(asctime)s - %(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('LOG.log'),
        logging.StreamHandler()
    ],
    encoding='utf-8'
)
logging.info("Loading Environment Variables")
load_dotenv()
logging.info("Loading Complete")

# Initialize AI models
logging.info("Setting up AI Models")
cyber = Cyber('multilingual', device='cpu')
logging.info("Setup Complete")

logging.info("Setting Up Analyzers")
youtube_comment_analyzer = CommentAnalyzer(cyber)
logging.info('Setup Complete')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM-BOT-TOKEN')

# Initialize Telegram Bot
# Initialize bot
telegramDataBase = TelegramDatabase()
bot = TelegramBot(token=TELEGRAM_BOT_TOKEN)

# 2. Add commands via decorators
@bot.command('start')
async def start(update, context):
    await update.message.reply_text("🚀 Bot started! Use /verify")

@bot.command('register')
async def register(update, context):
    await update.message.reply_text('Please wait!')
    content = (update.message.text)[9:].strip()
    with app.app_context():
        if User.query.filter_by(uuid=content).first():
            telegramDataBase.register_uuid(str(update.effective_user.id), content)
            await update.message.reply_text(f"Registration Sucessfull, Please varify the bot with /verify varification_code")
        else:
            await update.message.reply_text(f"Registration Failed. No Such registerd user exists")
@bot.command('verify')
async def verify(update, context):
    """Step 2: Verify using code from web"""
    if telegramDataBase.is_verified(update.effective_user.id):
        await update.message.reply_text("✅ Already verified!")
        return

    code = context.args[0] if context.args else None
    if not code:
        await update.message.reply_text("❌ Usage: /verify <code>")
        return

    if telegramDataBase.verify_code(update.effective_user.id, code):
        await update.message.reply_text(
            "🎉 Verification successful!\n"
            "You can now use all bot features"
        )
    else:
        await update.message.reply_text(
            "❌ Verification failed\n"
            "Possible reasons:\n"
            "- Wrong code\n"
            "- Code expired\n"
            "- No active registration\n"
            "Try /register again if needed"
        )
# 3. Set message handler (optional)
async def handle_message(update):
    await update.message.reply_text(f"📩 You said: {update.message.text}")

bot.message_handler = handle_message
bot.start()
# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form['username'].strip()
            email = request.form['email'].strip()
            password = request.form['password'].strip()

            if not username or not email or not password:
                flash('All fields are required', 'error')
                return redirect(url_for('signup'))

            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'error')
                return redirect(url_for('signup'))
                
            if User.query.filter_by(username=username).first():
                flash('Username already taken', 'error')
                return redirect(url_for('signup'))

            new_user = User(username=username, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user)
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Features
@app.route('/ytca')
def ytca():
    return render_template('ytca.html')

@app.route('/analyze', methods=['POST'])
def analyze_comments():
    video_url = request.form.get('url')
    results = youtube_comment_analyzer.analyse_comment(video_url, num_comments=150) 
    
    return jsonify({
        'hate': round(results['hate_comments'] / results['total_comments'] * 100, 2),
        'positive': round(results['positive_comments'] / results['total_comments'] * 100, 2),
        'neutral': round(results['neutral_comments'] / results['total_comments'] * 100, 2)
    })

# Debugger SQL 
@app.route('/debug_telegram_db')
def debug_telegram_db():
    cur = telegramDataBase.conn.execute("SELECT * FROM verification_codes")
    results = cur.fetchall()
    return jsonify([dict(row) for row in results])


# Bots 
@app.route('/bots')
@login_required
def bots():
    return render_template('bots.html')

@app.route('/tbs')
@login_required
def tbs():
    """Generate and display verification code"""
    """
    if not current_user.telegram_id:
        flash("Please link your Telegram account first", "error")
        return redirect(url_for('bots'))
    """
    if telegramDataBase.is_verified(telegramDataBase.get_telegram_id(current_user.uuid)):
        return redirect(url_for('telegram_bot'))
    else: 
        verification_code = telegramDataBase.generate_verification_code(current_user.uuid)
        
        #verification_code = Tbot.generate_verification_code(current_user.id)
        return render_template(
            'telegram_bot_setup.html',
            user_uuid = current_user.uuid,
            verification_code=verification_code,
        )

@app.route('/telegram-bot')
@login_required
def telegram_bot():
    t_id = telegramDataBase.get_telegram_id(current_user.uuid)
    isVerified = telegramDataBase.is_verified(t_id)
    if isVerified:
        return render_template(
            'telegram_bot.html',
            tid         = telegramDataBase.get_telegram_id(current_user.uuid), 
            uuid        = current_user.uuid
            )
    else:
        return redirect(url_for('tbs'))

@app.route('/check_telegram_verification')
@login_required
def check_telegram_verification():
    # Get the Telegram ID associated with the current user's UUID
    telegram_id = telegramDataBase.get_telegram_id(current_user.uuid)
    
    # Check if verified
    is_verified = telegramDataBase.is_verified(telegram_id) if telegram_id else False
    
    # Also update the user's verification status in the main database
    if is_verified and not current_user.telegram_verified:
        current_user.telegram_verified = True
        db.session.commit()
    
    return jsonify({
        'verified': is_verified,
        'telegram_id': telegram_id
    })

@app.route('/comming_soon')
def comming_soon():
    return render_template('under_development.html')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5050, debug=True, threaded=True)
    except:
        logging.error("ERROR RUNNING.")
    finally:
        bot.stop()