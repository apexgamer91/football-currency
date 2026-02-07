import sqlite3

# Connect to database (creates file if not exists)
conn = sqlite3.connect("football_currency.db")
cursor = conn.cursor()

cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("sushant", "2019000790"))


# --- Admins Table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    adminID INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")


# --- Admins Table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    adminID INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")


# --- Players Table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    playerID INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    balance INTEGER DEFAULT 0,
    bank_cash INTEGER DEFAULT 0,
    cash INTEGER DEFAULT 0,
    fc_coin INTEGER DEFAULT 0,
    card_limit INTEGER DEFAULT 0,
    registration_date TEXT,
    expiration_date TEXT,
    is_banned INTEGER DEFAULT 0,
    profile_pic TEXT
)
""")


# --- Messages Table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    messageID INTEGER PRIMARY KEY AUTOINCREMENT,
    senderID INTEGER NOT NULL,
    receiverID INTEGER NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# --- Support Table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS support (
    supportID INTEGER PRIMARY KEY AUTOINCREMENT,
    playerID INTEGER,
    issue TEXT NOT NULL,
    status TEXT DEFAULT 'Open',
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# --- Shop Items Table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS shop_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playerID INTEGER NOT NULL,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# --- Notices Table ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# Commit and close
conn.commit()
conn.close()

print("Database setup complete ✅")