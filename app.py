from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_NAME = "dicemint.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS balances (
            telegram_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id TEXT,
            new_user_id TEXT
        )''')
        conn.commit()

@app.route("/")
def home():
    return "✅ DiceMint Backend with SQLite is Live!"

@app.route("/get_balance", methods=["POST"])
def get_balance():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT balance FROM balances WHERE telegram_id = ?", (telegram_id,))
        row = c.fetchone()
        balance = row[0] if row else 0
    return jsonify({"balance": balance})

@app.route("/update_balance", methods=["POST"])
def update_balance():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))
    balance = int(data.get("balance", 0))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO balances (telegram_id, balance) VALUES (?, ?)", (telegram_id, balance))
        conn.commit()
    return jsonify({"success": True, "new_balance": balance})

@app.route("/claim_bonus", methods=["POST"])
def claim_bonus():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT balance FROM balances WHERE telegram_id = ?", (telegram_id,))
        row = c.fetchone()
        if row:
            bonus = 1000
            new_balance = row[0] + bonus
            c.execute("UPDATE balances SET balance = ? WHERE telegram_id = ?", (new_balance, telegram_id))
            conn.commit()
            return jsonify({"success": True, "new_balance": new_balance})
        else:
            return jsonify({"success": False, "message": "User not found"}), 404

@app.route("/api/referral", methods=["POST"])
def referral():
    data = request.get_json()
    new_user_id = str(data.get("new_user_id"))
    referrer_id = str(data.get("referrer_id"))

    if new_user_id == referrer_id:
        return jsonify({"status": "error", "message": "Self-referral is not allowed"}), 400

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Check if new user already exists
        c.execute("SELECT 1 FROM balances WHERE telegram_id = ?", (new_user_id,))
        if c.fetchone():
            return jsonify({"status": "skipped", "message": "User already registered"}), 200

        # Add new user
        c.execute("INSERT INTO balances (telegram_id, balance) VALUES (?, ?)", (new_user_id, 0))

        # Log referral
        c.execute("INSERT INTO referrals (referrer_id, new_user_id) VALUES (?, ?)", (referrer_id, new_user_id))

        # Update referrer's balance
        c.execute("SELECT balance FROM balances WHERE telegram_id = ?", (referrer_id,))
        row = c.fetchone()
        new_balance = (row[0] if row else 0) + 500
        c.execute("INSERT OR REPLACE INTO balances (telegram_id, balance) VALUES (?, ?)", (referrer_id, new_balance))

        conn.commit()
    return jsonify({"status": "success", "message": "Referral bonus added"}), 200

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)