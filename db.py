import sqlite3
conn = sqlite3.connect("exchange.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    mnemonic TEXT,
    btc_address TEXT,
    eth_address TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    coin TEXT,
    amount REAL,
    price REAL,
    status TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS escrows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id INTEGER,
    seller_id INTEGER,
    coin TEXT,
    amount REAL,
    status TEXT
)''')

conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

def add_user(user_id, mnemonic, btc, eth):
    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user_id, mnemonic, btc, eth))
    conn.commit()

def get_all_users():
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()
