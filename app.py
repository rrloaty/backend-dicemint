from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS balances (
            telegram_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id TEXT,
            new_user_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return "✅ DiceMint Backend (SQLite) is Live!"

@app.route("/get_balance", methods=["POST"])
def get_balance():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT balance FROM balances WHERE telegram_id = ?", (telegram_id,))
    row = c.fetchone()
    conn.close()

    return jsonify({"balance": row[0] if row else 0})

@app.route("/update_balance", methods=["POST"])
def update_balance():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))
    balance = int(data.get("balance", 0))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO balances (telegram_id, balance) VALUES (?, ?) ON CONFLICT(telegram_id) DO UPDATE SET balance = ?",
              (telegram_id, balance, balance))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "new_balance": balance})

@app.route("/claim_bonus", methods=["POST"])
def claim_bonus():
    telegram_id = str(request.json.get("telegram_id"))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT balance FROM balances WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()

    if user and user[0] >= 1000:
        conn.close()
        return jsonify({"success": False, "message": "Already claimed"})

    c.execute("INSERT INTO balances (telegram_id, balance) VALUES (?, 1000) ON CONFLICT(telegram_id) DO UPDATE SET balance = balance + 1000", (telegram_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "$10 bonus added"})

@app.route("/api/referral", methods=["POST"])
def referral():
    data = request.get_json()
    new_user_id = str(data.get("new_user_id"))
    referrer_id = str(data.get("referrer_id"))

    if new_user_id == referrer_id:
        return jsonify({"status": "error", "message": "Self-referral not allowed"}), 400

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM balances WHERE telegram_id = ?", (new_user_id,))
    if c.fetchone():
        conn.close()
        return jsonify({"status": "skipped", "message": "Already registered"}), 200

    c.execute("INSERT INTO balances (telegram_id, balance) VALUES (?, 0)", (new_user_id,))
    c.execute("INSERT INTO referrals (referrer_id, new_user_id) VALUES (?, ?)", (referrer_id, new_user_id))

    # Give $5 bonus (500 coins) to referrer
    c.execute("INSERT INTO balances (telegram_id, balance) VALUES (?, 500) ON CONFLICT(telegram_id) DO UPDATE SET balance = balance + 500", (referrer_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "Referral successful"}), 200

if __name__ == "__main__":
    app.run(debug=True)