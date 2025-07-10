from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect("dice.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return "✅ DiceMint SQLite Backend is Live!"

@app.route("/get_balance", methods=["POST"])
def get_balance():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))
    conn = sqlite3.connect("dice.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    balance = row[0] if row else 0
    return jsonify({"balance": balance})

@app.route("/update_balance", methods=["POST"])
def update_balance():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))
    balance = int(data.get("balance", 0))

    conn = sqlite3.connect("dice.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()

    if row:
        cursor.execute("UPDATE users SET balance = ? WHERE telegram_id = ?", (balance, telegram_id))
    else:
        cursor.execute("INSERT INTO users (telegram_id, balance) VALUES (?, ?)", (telegram_id, balance))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "new_balance": balance})

@app.route("/api/referral", methods=["POST"])
def referral():
    data = request.get_json()
    new_user_id = str(data.get("new_user_id"))
    referrer_id = str(data.get("referrer_id"))

    if new_user_id == referrer_id:
        return jsonify({"status": "error", "message": "Self-referral is not allowed"}), 400

    conn = sqlite3.connect("dice.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (new_user_id,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"status": "skipped", "message": "User already registered"}), 200

    cursor.execute("INSERT INTO users (telegram_id, balance) VALUES (?, ?)", (new_user_id, 0))

    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (referrer_id,))
    row = cursor.fetchone()
    ref_balance = row[0] if row else 0
    ref_balance += 500

    cursor.execute("INSERT OR REPLACE INTO users (telegram_id, balance) VALUES (?, ?)", (referrer_id, ref_balance))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Referral successful"}), 200

# ✅ Route to view all user balances
@app.route("/all_users", methods=["GET"])
def all_users():
    conn = sqlite3.connect("dice.db")
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id, balance FROM users")
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

if __name__ == "__main__":
    app.run(debug=True)