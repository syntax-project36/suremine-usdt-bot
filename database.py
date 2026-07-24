# database.py

import sqlite3

DB_NAME = "suremine.db"
REFERRAL_BONUS = 25.0  # Amount credited per referral

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            referrer_id INTEGER,
            balance REAL DEFAULT 0.0,
            total_withdrawn REAL DEFAULT 0.0,
            payout_wallet TEXT DEFAULT 'Not Set'
        )
    """)

    # Create miners table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_miners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            miner_id TEXT,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create deposits/orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            miner_id TEXT,
            crypto TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create withdrawals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            status TEXT DEFAULT 'pending',
            tx_hash TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_user(user_id, username, first_name, referrer_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        if referrer_id == user_id:
            referrer_id = None

        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, referrer_id) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, referrer_id)
        )

        # Automatically credit referral bonus to inviter
        if referrer_id:
            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (REFERRAL_BONUS, referrer_id)
            )

        conn.commit()

    conn.close()

def set_wallet(user_id, wallet_address):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET payout_wallet = ? WHERE user_id = ?", (wallet_address, user_id))
    conn.commit()
    conn.close()

def get_dashboard_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    user = get_user(user_id)

    cursor.execute("SELECT COUNT(*) as ref_count FROM users WHERE referrer_id = ?", (user_id,))
    ref_count = cursor.fetchone()["ref_count"]

    cursor.execute("SELECT miner_id, COUNT(*) as count FROM user_miners WHERE user_id = ? GROUP BY miner_id", (user_id,))
    miners = cursor.fetchall()
    miners_count = {m["miner_id"]: m["count"] for m in miners}

    conn.close()
    return user, ref_count, miners_count

def calculate_uncollected_earnings(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT miner_id, 
               (strftime('%s', 'now') - strftime('%s', last_collected)) / 3600.0 as hours_passed
        FROM user_miners 
        WHERE user_id = ?
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()

    from miners import MINERS

    total_uncollected = 0.0
    tier_stats = {
        "miner_v1": {"count": 0, "mined": 0.0},
        "miner_v2": {"count": 0, "mined": 0.0},
        "miner_v3": {"count": 0, "mined": 0.0}
    }

    for row in rows:
        m_id = row["miner_id"]
        hours = max(0.0, row["hours_passed"])
        if m_id in MINERS:
            hourly_rate = MINERS[m_id]["hourly"]
            mined = hours * hourly_rate
            total_uncollected += mined
            
            if m_id in tier_stats:
                tier_stats[m_id]["count"] += 1
                tier_stats[m_id]["mined"] += mined

    return total_uncollected, tier_stats

def collect_profit(user_id):
    total_uncollected, _ = calculate_uncollected_earnings(user_id)
    if total_uncollected <= 0:
        return 0.0

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (total_uncollected, user_id))
    cursor.execute("UPDATE user_miners SET last_collected = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

    return total_uncollected

def create_order(user_id, miner_id, crypto):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, miner_id, crypto) VALUES (?, ?, ?)",
        (user_id, miner_id, crypto)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def approve_deposit(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE id = ? AND status = 'pending'", (order_id,))
    order = cursor.fetchone()

    if order:
        cursor.execute("UPDATE orders SET status = 'approved' WHERE id = ?", (order_id,))
        cursor.execute(
            "INSERT INTO user_miners (user_id, miner_id) VALUES (?, ?)",
            (order["user_id"], order["miner_id"])
        )
        conn.commit()

    conn.close()
    return order

def request_withdrawal(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()

    user = get_user(user_id)
    if amount < 300:
        conn.close()
        return False, "❌ Minimum withdrawal is *300 USDŦ*."

    if user["balance"] < amount:
        conn.close()
        return False, "❌ Insufficient balance!"

    if user["payout_wallet"] == "Not Set":
        conn.close()
        return False, "❌ Please set your Payout Wallet first!"

    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
    cursor.execute("INSERT INTO withdrawals (user_id, amount) VALUES (?, ?)", (user_id, amount))
    withdrawal_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return True, withdrawal_id

def approve_withdrawal_db(withdrawal_id, tx_hash):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM withdrawals WHERE id = ? AND status = 'pending'", (withdrawal_id,))
    w = cursor.fetchone()

    if w:
        cursor.execute("UPDATE withdrawals SET status = 'approved', tx_hash = ? WHERE id = ?", (tx_hash, withdrawal_id))
        cursor.execute("UPDATE users SET total_withdrawn = total_withdrawn + ? WHERE user_id = ?", (w["amount"], w["user_id"]))
        conn.commit()

    conn.close()
    return w

def admin_add_balance(user_id, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_all_user_ids():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [r["user_id"] for r in rows]