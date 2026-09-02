import asyncio
import json
import sqlite3
import time
import requests
import urllib.parse
from datetime import datetime
from threading import Thread
from flask import Flask, request, jsonify, render_template_string
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from apscheduler.schedulers.background import BackgroundScheduler

# ========== CONFIG ==========
BOT_TOKEN = "8945533096:AAEVcJ_58_0U1whnxwY5HIxyTp1SsEzsglw"
CHANNEL_ID = "-1003915320301"
CHANNEL_LINK = "https://t.me/S4DlI5E"
ATF_URL = "https://atfminers.asloni.online/miner/index.php"
OWNER = "@xghostid"

# ========== YOUR LINK AND COOKIE (PRE-ADDED) ==========
YOUR_TG_ID = "8497620413"
YOUR_LINK = "https://atfminers.asloni.online/miner/index.html?v=1786140012#tgWebAppData=user%3D%257B%2522id%2522%253A8497620413%252C%2522first_name%2522%253A%2522%25E2%259C%25A7%25CB%259A%25E2%2582%258A%25E2%2580%25A7%25E2%2581%25BA%25CB%2596%25E2%2599%25A1%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522username%2522%253A%2522xghostid%2522%252C%2522language_code%2522%253A%2522en%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FPks3N73UAgvoRUmpYME3h1v31Z_RFwc8YXnZDeIcHgnpsQZA884aVJjR4-4L8XPa.svg%2522%257D%26chat_instance%3D-968499519986194590%26chat_type%3Dsender%26auth_date%3D1788372127%26signature%3D9nlbLAPTBTsFgMMk55AoyrC3WOqON4MXUAfEBYLJSBufD2u3G2QCTGIvAa19aIz-A_-lmIMPNxn4Ogqqb9lQBA%26hash%3De16352f1bf1356b02788a3c45b86f7c4880a71242d9494dcdab0b962e91d41ab&tgWebAppVersion=9.6&tgWebAppPlatform=android&tgWebAppFullscreen=1&tgWebAppThemeParams=%7B%22bg_color%22%3A%22%231e1e1e%22%2C%22section_bg_color%22%3A%22%23181819%22%2C%22secondary_bg_color%22%3A%22%23000000%22%2C%22text_color%22%3A%22%23ffffff%22%2C%22hint_color%22%3A%22%237d7d7d%22%2C%22link_color%22%3A%22%237590e2%22%2C%22button_color%22%3A%22%23517af7%22%2C%22button_text_color%22%3A%22%23ffffff%22%2C%22header_bg_color%22%3A%22%23242326%22%2C%22accent_text_color%22%3A%22%23839ef0%22%2C%22section_header_text_color%22%3A%22%238b9ff9%22%2C%22subtitle_text_color%22%3A%22%237e7e7f%22%2C%22destructive_text_color%22%3A%22%23ee686f%22%2C%22section_separator_color%22%3A%22%23000000%22%2C%22bottom_bar_bg_color%22%3A%22%23000000%22%7D"
YOUR_COOKIE = "eyJ0Z19pZC16ljg00Tc2MjA0MTMiLCJpaC16ljUwZmM0NzA4MjhiYjThZGQyMTkxZWYxODewNzFjZGE2YjVkOWE4MTZhMjVhZmYzNjZjMjIzMzF2IN2YXjg2NTYliLCJ1YSI6IiIsImhzdiC16lmFoZ1m1pbmVycy5hc2xvbmkub25saW5lliwiaWF0IjoxNzg4MzgwNTU0LCJleHAiOjE3ODg1NTMzNTR9.RyZXi4IBP9Mr5SQTDviueeaw0BiOM-sOYtD9P3Tn_O8"

# ========== DATABASE ==========
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        tg_id TEXT PRIMARY KEY,
        link TEXT,
        cookie TEXT,
        balance REAL DEFAULT 0,
        pool REAL DEFAULT 0,
        holding REAL DEFAULT 0,
        level INTEGER DEFAULT 1,
        progress REAL DEFAULT 0,
        tasks TEXT DEFAULT '[]',
        last_task TEXT,
        last_claim TEXT,
        next_claim TEXT,
        active INTEGER DEFAULT 1,
        first_name TEXT,
        username TEXT
    )''')
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

init_db()

def db():
    return sqlite3.connect('bot.db')

# ========== ATF API ==========
def call_atf(tg_data, cookie, action, extra=None):
    t = int(time.time() * 1000)
    url = f"{ATF_URL}?action={action}&t={t}"
    payload = {"tgWebAppData": tg_data}
    if extra: payload.update(extra)
    
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Linux; Android 14)",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://atfminers.asloni.online",
        "Referer": "https://atfminers.asloni.online/miner/index.html?v=1786140012"
    })
    sess.cookies.set("atf_tma_session", cookie)
    
    try:
        r = sess.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()
        return {"status": "error", "code": r.status_code}
    except Exception as e:
        print(f"API Error: {e}")
        return {"status": "error"}

def extract_tg_data(link):
    parsed = urllib.parse.urlparse(link)
    params = urllib.parse.parse_qs(parsed.query)
    return params.get('tgWebAppData', [None])[0]

# ========== SYNC USER ==========
def sync_user(tg_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT link, cookie FROM users WHERE tg_id = ?", (tg_id,))
    user = c.fetchone()
    conn.close()

    if not user or not user[0] or not user[1]:
        print(f"[SYNC] {tg_id}: Missing link or cookie")
        return False

    tg_data = extract_tg_data(user[0])
    if not tg_data:
        print(f"[SYNC] {tg_id}: No tgWebAppData")
        return False

    res = call_atf(tg_data, user[1], "sync_wallet")

    if res.get("status") != "success":
        print(f"[SYNC ERROR] {tg_id}: {res}")
        return False

    try:
        data = res.get("user", {})
        mined = float(data.get("mined_balance", 0))
        holding = float(data.get("wallet_holding_atf", 0))
        balance = float(data.get("assets_total", mined + holding))
        level = int(data.get("miner_level", 1))
        progress = float(data.get("level_pending_withdraw_atf", 0))
        completed = data.get("completed_tasks", [])

        conn = db()
        c = conn.cursor()
        c.execute("""UPDATE users SET pool = ?, holding = ?, balance = ?, level = ?, progress = ?, tasks = ?, last_task = CURRENT_TIMESTAMP WHERE tg_id = ?""",
                  (mined, holding, balance, level, progress, json.dumps(completed), tg_id))
        conn.commit()
        conn.close()

        print(f"[SYNC] {tg_id} | Balance={balance} | Level={level}")
        return True
    except Exception as e:
        print(f"[SYNC ERROR] {tg_id}: {e}")
        return False

# ========== DO TASKS ==========
def do_tasks(tg_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT link, cookie, tasks FROM users WHERE tg_id = ?", (tg_id,))
    user = c.fetchone()
    conn.close()
    if not user or not user[1]: return
    
    tg_data = extract_tg_data(user[0])
    if not tg_data: return
    
    tasks = ["telegram_join", "telegram_join_fa", "twitter_follow", "youtube_subscribe", "telegram_react_latest", "website_visit", "youtube_like_comment", "twitter_retweet"]
    done = json.loads(user[2] or '[]')
    
    for task in tasks:
        if task in done: continue
        res = call_atf(tg_data, user[1], task)
        if res.get("status") == "success":
            done.append(task)
        time.sleep(1.5)
    
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET tasks = ?, last_task = CURRENT_TIMESTAMP WHERE tg_id = ?", (json.dumps(done), tg_id))
    conn.commit()
    conn.close()

# ========== CLAIM REWARDS ==========
def claim_rewards(tg_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT link, cookie FROM users WHERE tg_id = ?", (tg_id,))
    user = c.fetchone()
    conn.close()
    if not user or not user[1]: return
    
    tg_data = extract_tg_data(user[0])
    if not tg_data: return
    
    res = call_atf(tg_data, user[1], "claim")
    if res.get("status") == "success":
        data = res.get("user", {})
        new_mined = float(data.get("mined_balance", 0))
        holding = float(data.get("wallet_holding_atf", 0))
        balance = float(data.get("assets_total", new_mined + holding))
        
        conn = db()
        c = conn.cursor()
        c.execute("UPDATE users SET pool = ?, holding = ?, balance = ?, last_claim = CURRENT_TIMESTAMP, next_claim = datetime('now', '+6 hours') WHERE tg_id = ?",
                  (new_mined, holding, balance, tg_id))
        conn.commit()
        conn.close()
        print(f"[CLAIM] {tg_id}: {balance} ATF")

# ========== PROCESS USER ==========
def process_user(tg_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT last_task, last_claim FROM users WHERE tg_id = ?", (tg_id,))
    data = c.fetchone()
    conn.close()
    if not data: return
    
    sync_user(tg_id)
    
    if data[0]:
        try:
            hours = (datetime.now() - datetime.strptime(data[0], '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600
            if hours >= 2: do_tasks(tg_id)
        except: pass
    
    if data[1]:
        try:
            hours = (datetime.now() - datetime.strptime(data[1], '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600
            if hours >= 6: claim_rewards(tg_id)
        except: pass
    
    sync_user(tg_id)

def process_all():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT tg_id FROM users WHERE active = 1")
    users = c.fetchall()
    conn.close()
    for u in users:
        try: process_user(u[0])
        except Exception as e:
            print(f"Error processing {u[0]}: {e}")
            # ========== FLASK APP ==========
app = Flask(__name__)

HTML_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>ATF Bot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:system-ui;background:#0a0a1a;color:#fff;padding:15px}
        .container{max-width:1000px;margin:auto}
        h1{text-align:center;font-size:22px;margin-bottom:20px;color:#4a9eff}
        .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:10px;margin-bottom:20px}
        .stat{background:rgba(255,255,255,0.03);padding:15px;border-radius:10px;text-align:center;border:1px solid rgba(255,255,255,0.05)}
        .stat .num{font-size:26px;font-weight:700;color:#4a9eff}
        .stat .lbl{font-size:11px;color:#667788;margin-top:4px}
        .card{background:rgba(255,255,255,0.03);border-radius:10px;padding:12px 15px;margin-bottom:8px;border:1px solid rgba(255,255,255,0.05)}
        .row{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
        .name{font-weight:600;font-size:14px}
        .id{color:#667788;font-size:11px}
        .bal{color:#4a9eff;font-weight:600;font-size:15px}
        .level{color:#8899bb;font-size:12px}
        .status{font-size:11px;padding:2px 10px;border-radius:20px}
        .online{color:#00b894;background:rgba(0,184,148,0.1)}
        .offline{color:#ff6b6b;background:rgba(255,107,107,0.1)}
        .time{color:#667788;font-size:11px}
        .footer{text-align:center;margin-top:30px;color:#667788;font-size:12px;border-top:1px solid rgba(255,255,255,0.05);padding-top:15px}
        .refresh-btn{background:#4a9eff;border:none;color:#fff;padding:6px 16px;border-radius:6px;cursor:pointer;font-size:12px}
        .refresh-btn:hover{opacity:0.8}
        .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;flex-wrap:wrap;gap:10px}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 ATF Dashboard</h1>
            <button class="refresh-btn" onclick="load()">🔄 Refresh</button>
        </div>
        <div class="stats">
            <div class="stat"><div class="num" id="total">0</div><div class="lbl">Users</div></div>
            <div class="stat"><div class="num" id="bal">0</div><div class="lbl">Total ATF</div></div>
            <div class="stat"><div class="num" id="active">0</div><div class="lbl">Active</div></div>
            <div class="stat"><div class="num" id="avg">0</div><div class="lbl">Avg Level</div></div>
        </div>
        <div id="users"></div>
        <div class="footer">🤖 Powered by Hashu | 💬 @xghostid</div>
    </div>
    <script>
        async function load(){
            try{
                const r=await fetch('/api/users');
                const data=await r.json();
                document.getElementById('total').textContent=data.total;
                document.getElementById('bal').textContent=data.total_balance.toFixed(2);
                document.getElementById('active').textContent=data.active;
                document.getElementById('avg').textContent=data.avg_level.toFixed(1);
                let html='';
                data.users.forEach(u=>{
                    html+=`
                    <div class="card">
                        <div class="row">
                            <div>
                                <div class="name">${u.name}</div>
                                <div class="id">ID: ${u.tg_id}</div>
                            </div>
                            <div style="text-align:right">
                                <div class="bal">${u.balance.toFixed(4)} ATF</div>
                                <div class="level">Level ${u.level} (${u.progress}%)</div>
                            </div>
                        </div>
                        <div class="row" style="margin-top:6px">
                            <span class="time">⏳ ${u.next_claim || 'Ready'}</span>
                            <span class="status ${u.active?'online':'offline'}">${u.active?'🟢 Active':'🔴 Offline'}</span>
                        </div>
                    </div>
                    `;
                });
                document.getElementById('users').innerHTML = html || '<div style="text-align:center;padding:40px;color:#667788">No users added yet</div>';
            }catch(e){}
        }
        load();
        setInterval(load, 30000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_DASHBOARD)

@app.route('/api/users')
def get_users():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT tg_id, balance, level, progress, next_claim, active, first_name, username FROM users")
    users = c.fetchall()
    conn.close()
    
    result = []
    total_bal = 0
    active = 0
    total_level = 0
    
    for u in users:
        total_bal += u[1]
        total_level += u[2]
        if u[5]: active += 1
        name = u[6] or u[7] or u[0][:8]
        result.append({
            'tg_id': u[0],
            'name': name,
            'balance': u[1],
            'level': u[2],
            'progress': round(u[3], 1),
            'next_claim': u[4],
            'active': bool(u[5])
        })
    
    return jsonify({
        'users': result,
        'total': len(result),
        'total_balance': total_bal,
        'active': active,
        'avg_level': total_level / len(result) if result else 0
    })

@app.route('/api/add', methods=['POST'])
def add_user():
    data = request.json
    tg_id = data.get('tg_id')
    link = data.get('link')
    cookie = data.get('cookie')
    name = data.get('name', '')
    
    if not all([tg_id, link, cookie]):
        return jsonify({'error': 'Missing data'}), 400
    
    conn = db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (tg_id, link, cookie, first_name) VALUES (?, ?, ?, ?)", 
              (tg_id, link, cookie, name))
    conn.commit()
    conn.close()
    
    sync_user(tg_id)
    return jsonify({'ok': True})

@app.route('/api/balance/<tg_id>')
def get_balance(tg_id):
    sync_user(tg_id)
    conn = db()
    c = conn.cursor()
    c.execute("SELECT balance, level, progress, next_claim FROM users WHERE tg_id = ?", (tg_id,))
    user = c.fetchone()
    conn.close()
    if not user: return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'balance': round(user[0], 4),
        'level': user[1],
        'progress': round(user[2], 1),
        'next_claim': user[3] or 'Ready'
    })

@app.route('/api/refresh/<tg_id>')
def refresh_user(tg_id):
    process_user(tg_id)
    return jsonify({'ok': True})

@app.route('/api/debug/<tg_id>')
def debug_user(tg_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = c.fetchone()
    conn.close()
    if not user:
        return jsonify({'error': 'User not found'})
    return jsonify({
        'tg_id': user[0],
        'has_link': bool(user[1]),
        'has_cookie': bool(user[2]),
        'balance': user[3],
        'level': user[6]
    })
    # ========== AUTO ADD YOUR ACCOUNT ==========
def auto_add_your_account():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT tg_id FROM users WHERE tg_id = ?", (YOUR_TG_ID,))
    exists = c.fetchone()
    
    if not exists:
        c.execute("INSERT INTO users (tg_id, link, cookie, first_name, username) VALUES (?, ?, ?, ?, ?)", 
                  (YOUR_TG_ID, YOUR_LINK, YOUR_COOKIE, "Hashu", "xghostid"))
        conn.commit()
        print(f"✅ Auto-added your account: {YOUR_TG_ID}")
    else:
        c.execute("UPDATE users SET link = ?, cookie = ? WHERE tg_id = ?", 
                  (YOUR_LINK, YOUR_COOKIE, YOUR_TG_ID))
        conn.commit()
        print(f"✅ Updated your account: {YOUR_TG_ID}")
    
    conn.close()
    sync_user(YOUR_TG_ID)

# ========== TELEGRAM BOT ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def is_member(user_id):
    try:
        m = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False

# ========== COLORED BUTTONS ==========
def get_menu():
    return {
        "inline_keyboard": [
            [{"text": "🍪 Add Cookie", "callback_data": "add", "style": "primary"}, {"text": "💰 Balance", "callback_data": "bal", "style": "success"}],
            [{"text": "📊 Stats", "callback_data": "stats", "style": "primary"}, {"text": "⛏️ Mine Now", "callback_data": "mine", "style": "success"}],
            [{"text": "💬 Support", "url": "https://t.me/xghostid", "style": "danger"}]
        ]
    }

def get_back():
    return {"inline_keyboard": [[{"text": "🔙 Back", "callback_data": "back", "style": "danger"}]]}

def get_join():
    return {"inline_keyboard": [[{"text": "🔔 Join Channel", "url": CHANNEL_LINK, "style": "primary"}], [{"text": "✅ I've Joined", "callback_data": "joined", "style": "success"}]]}

# ========== BOT HANDLERS ==========
@dp.message(Command("start"))
async def start(msg: types.Message):
    tg_id = str(msg.from_user.id)
    name = msg.from_user.first_name or "User"
    username = msg.from_user.username or ""
    
    if not await is_member(tg_id):
        await msg.answer(f"👋 Welcome {name}!\n\n⚠️ Please join our channel first.\n\n🔗 {CHANNEL_LINK}", reply_markup=get_join(), parse_mode=ParseMode.HTML)
        return
    
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET first_name = ?, username = ? WHERE tg_id = ?", (name, username, tg_id))
    c.execute("SELECT balance FROM users WHERE tg_id = ?", (tg_id,))
    user = c.fetchone()
    conn.commit()
    conn.close()
    
    text = "🚀 <b>ATF Bot</b>\n\n"
    if user:
        text += f"💰 Balance: <code>{user[0]:.4f}</code> ATF\n"
    else:
        text += "❌ No account linked\n\nClick <b>Add Cookie</b> to setup"
    text += "\n\nSelect option:"
    
    await msg.answer(text, reply_markup=get_menu(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "joined")
async def joined(call: types.CallbackQuery):
    if await is_member(str(call.from_user.id)):
        await call.message.delete()
        await start(call.message)
    else:
        await call.answer("❌ Not joined yet!", show_alert=True)

@dp.callback_query(F.data == "add")
async def add_cookie(call: types.CallbackQuery):
    await call.message.edit_text("🍪 <b>Send your cookie</b>\n\n📌 How to get:\n1. Open ATF in browser\n2. F12 → Application → Cookies\n3. Copy <code>atf_tma_session</code> value", reply_markup=get_back(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "bal")
async def balance(call: types.CallbackQuery):
    tg_id = str(call.from_user.id)
    await call.answer("Fetching...")
    sync_user(tg_id)
    
    conn = db()
    c = conn.cursor()
    c.execute("SELECT balance, level, progress FROM users WHERE tg_id = ?", (tg_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        await call.message.answer("❌ No account found!", reply_markup=get_menu())
        return
    
    text = f"💰 <b>Your Balance</b>\n\n💎 Balance: <code>{user[0]:.4f}</code> ATF\n📈 Level: {user[1]}\n📊 Progress: {user[2]:.1f}%"
    await call.message.answer(text, reply_markup=get_menu(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "stats")
async def stats(call: types.CallbackQuery):
    tg_id = str(call.from_user.id)
    await call.answer("Loading...")
    sync_user(tg_id)
    
    conn = db()
    c = conn.cursor()
    c.execute("SELECT balance, level, progress, next_claim, last_task, last_claim FROM users WHERE tg_id = ?", (tg_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        await call.message.answer("❌ No account found!", reply_markup=get_menu())
        return
    
    text = f"📊 <b>Mining Stats</b>\n\n💰 Balance: <code>{user[0]:.4f}</code> ATF\n📈 Level: {user[1]}\n📊 Progress: {user[2]:.1f}%\n⏳ Next Claim: {user[3] or 'Ready'}\n🔄 Last Tasks: {user[4] or 'Never'}\n💰 Last Claim: {user[5] or 'Never'}"
    await call.message.answer(text, reply_markup=get_menu(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "mine")
async def mine(call: types.CallbackQuery):
    tg_id = str(call.from_user.id)
    await call.answer("⛏️ Mining started!", show_alert=True)
    process_user(tg_id)
    await call.message.answer("✅ Mining completed!\n\nCheck your balance with Balance button.", reply_markup=get_menu())

@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):
    await call.message.delete()
    await start(call.message)

@dp.message(F.text)
async def handle_text(msg: types.Message):
    text = msg.text.strip()
    tg_id = str(msg.from_user.id)
    name = msg.from_user.first_name or "User"
    username = msg.from_user.username or ""
    
    if "atfminers.asloni.online" in text and "tgWebAppData" in text:
        conn = db()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (tg_id, link, first_name, username) VALUES (?, ?, ?, ?)", (tg_id, text, name, username))
        conn.commit()
        conn.close()
        await msg.answer("✅ <b>Link saved!</b>\n\nNow send your <b>Cookie</b> 🍪", reply_markup=get_back(), parse_mode=ParseMode.HTML)
        return
    
    if "eyJ" in text and len(text) > 50:
        conn = db()
        c = conn.cursor()
        c.execute("SELECT link FROM users WHERE tg_id = ?", (tg_id,))
        user = c.fetchone()
        conn.close()
        
        if not user or not user[0]:
            await msg.answer("❌ <b>Link not found!</b>\n\nFirst send your ATF link, then cookie.", reply_markup=get_back(), parse_mode=ParseMode.HTML)
            return
        
        conn = db()
        c = conn.cursor()
        c.execute("UPDATE users SET cookie = ? WHERE tg_id = ?", (text, tg_id))
        conn.commit()
        conn.close()
        
        sync_user(tg_id)
        
        conn = db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE tg_id = ?", (tg_id,))
        user = c.fetchone()
        conn.close()
        
        if user and user[0] > 0:
            await msg.answer(f"✅ <b>Cookie saved!</b>\n\n💰 Balance: <code>{user[0]:.4f}</code> ATF\n\nBot is now active! 🚀", reply_markup=get_menu(), parse_mode=ParseMode.HTML)
        else:
            await msg.answer("✅ <b>Cookie saved!</b>\n\nSyncing data... Please wait a moment.\nThen click 'Balance' to check.", reply_markup=get_menu(), parse_mode=ParseMode.HTML)
        return
    
    await msg.answer("❌ <b>Invalid input!</b>\n\nSend either:\n• ATF link (full URL with tgWebAppData)\n• Cookie (atf_tma_session value)", reply_markup=get_menu(), parse_mode=ParseMode.HTML)

# ========== SCHEDULER ==========
scheduler = BackgroundScheduler()
scheduler.add_job(process_all, 'interval', minutes=15)
scheduler.start()

# ========== RUN BOTH ==========
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

async def run_bot():
    auto_add_your_account()
    print("=" * 40)
    print("🚀 ATF Bot Started")
    print("📊 Dashboard: http://localhost:5000")
    print("💬 Support: @xghostid")
    print(f"✅ Your Account: {YOUR_TG_ID}")
    print("🔄 Auto tasks every 2 hours")
    print("💰 Auto claim every 6 hours")
    print("=" * 40)
    await dp.start_polling(bot)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot())