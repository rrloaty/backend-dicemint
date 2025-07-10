from flask import Flask, request, jsonify
from flask_cors import CORS
from tinydb import TinyDB, Query

app = Flask(__name__)
CORS(app)

db = TinyDB("db.json")
balances = db.table("balances")
referrals = db.table("referrals")

@app.route("/")
def home():
    return "✅ DiceMint Backend with TinyDB is Live!"

@app.route("/get_balance", methods=["POST"])
def get_balance():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))
    user = balances.get(Query().telegram_id == telegram_id)
    balance = user["balance"] if user else 0
    return jsonify({"balance": balance})

@app.route("/update_balance", methods=["POST"])
def update_balance():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))
    balance = data.get("balance", 0)
    if balances.contains(Query().telegram_id == telegram_id):
        balances.update({"balance": balance}, Query().telegram_id == telegram_id)
    else:
        balances.insert({"telegram_id": telegram_id, "balance": balance})
    return jsonify({"success": True, "new_balance": balance})

@app.route("/claim_bonus", methods=["POST"])
def claim_bonus():
    data = request.get_json()
    telegram_id = str(data.get("telegram_id"))
    if referrals.contains(Query().telegram_id == telegram_id):
        return jsonify({"success": False, "message": "Already claimed"})
    user = balances.get(Query().telegram_id == telegram_id)
    if user:
        new_balance = user["balance"] + 1000
        balances.update({"balance": new_balance}, Query().telegram_id == telegram_id)
    else:
        balances.insert({"telegram_id": telegram_id, "balance": 1000})
    referrals.insert({"telegram_id": telegram_id})
    return jsonify({"success": True})

@app.route("/api/referral", methods=["POST"])
def referral():
    data = request.get_json()
    new_user_id = str(data.get("new_user_id"))
    referrer_id = str(data.get("referrer_id"))

    if new_user_id == referrer_id:
        return jsonify({"status": "error", "message": "Self-referral is not allowed"}), 400

    if balances.contains(Query().telegram_id == new_user_id):
        return jsonify({"status": "skipped", "message": "User already registered"}), 200

    balances.insert({"telegram_id": new_user_id, "balance": 0})
    referrals.insert({"referrer": referrer_id, "new_user": new_user_id})

    ref_user = balances.get(Query().telegram_id == referrer_id)
    new_balance = (ref_user["balance"] if ref_user else 0) + 500
    if ref_user:
        balances.update({"balance": new_balance}, Query().telegram_id == referrer_id)
    else:
        balances.insert({"telegram_id": referrer_id, "balance": new_balance})

    return jsonify({"status": "success", "message": "Referral successful"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)