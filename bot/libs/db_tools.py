import sqlite3
import os


def connect_to_db():
    db_path = (os.getenv('DB_URL', 'sqlite:///db.sqlite3')
               .replace("sqlite:///", ""))
    conn = sqlite3.connect(db_path)
    return conn


def save_user(user_id, chat_id, full_name, tg_username):
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            full_name TEXT,
            tg_username TEXT
        )
    ''')

    cursor.execute('''
        INSERT OR IGNORE INTO users (telegram_id, chat_id, full_name, tg_username)
        VALUES (?, ?, ?, ?)
    ''', (user_id, chat_id, full_name, tg_username))

    conn.commit()
    conn.close()
