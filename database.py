# database.py
# This file manages all database operations for the Mavericks Platform.

import sqlite3
from datetime import date, timedelta
import json

def get_db_connection():
    """Establishes and returns a connection to the database."""
    conn = sqlite3.connect("mavericks.db", check_same_thread=False)
    # This allows accessing columns by name, which is much cleaner
    conn.row_factory = sqlite3.Row 
    return conn

def setup_database():
    """Sets up the database tables and adds new columns if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        password TEXT,
        skill TEXT,
        gems INTEGER DEFAULT 0,
        badge TEXT DEFAULT 'Newbie',
        streak INTEGER DEFAULT 0,
        last_login TEXT DEFAULT CURRENT_DATE,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        assessment_scores TEXT,
        resume_text TEXT
    )
    ''')
    
    # Safely add columns if they don't exist to avoid errors on subsequent runs
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN assessment_scores TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN resume_text TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN gems INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass


    conn.commit()
    conn.close()

def create_user(name, password, skill):
    """Creates a new user in the database."""
    conn = get_db_connection()
    try:
        conn.cursor().execute("INSERT INTO users (name, password, skill, assessment_scores) VALUES (?, ?, ?, ?)", 
                              (name, password, skill, '{}'))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # This happens if the username already exists
    finally:
        conn.close()

def get_user_by_credentials(name, password):
    """Fetches a user by their name and password for login."""
    conn = get_db_connection()
    user = conn.cursor().execute("SELECT * FROM users WHERE name=? AND password=?", (name, password)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_name(name):
    """Fetches the latest user data by name."""
    conn = get_db_connection()
    user = conn.cursor().execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    """NEW: Fetches all users from the database for batch updates."""
    conn = get_db_connection()
    users = conn.cursor().execute("SELECT name, gems, badge FROM users").fetchall()
    conn.close()
    return [dict(user) for user in users]

def update_login_streak(name):
    """Updates a user's login streak based on the last login date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_login, streak FROM users WHERE name=?", (name,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return
        
    last_login, streak = result['last_login'], result['streak']
    today = date.today()
    
    if last_login != str(today): # Only update if it's a new day
        if last_login == str(today - timedelta(days=1)):
            streak += 1
        else:
            streak = 1 # Reset streak if they missed a day
        cursor.execute("UPDATE users SET streak=?, last_login=?, last_active=CURRENT_TIMESTAMP WHERE name=?", 
                       (streak, str(today), name))
        conn.commit()
    conn.close()

def update_user_gems(name, gems_to_add):
    """Adds a specified number of gems to a user's account."""
    conn = get_db_connection()
    conn.cursor().execute("UPDATE users SET gems = gems + ? WHERE name=?", (gems_to_add, name))
    conn.commit()
    conn.close()

def update_user_badge(name, new_badge):
    """Updates a user's badge in the database."""
    conn = get_db_connection()
    conn.cursor().execute("UPDATE users SET badge=? WHERE name=?", (new_badge, name))
    conn.commit()
    conn.close()
    
def batch_update_badges(users_to_update):
    """NEW: Updates the badges for a list of users in a single transaction."""
    conn = get_db_connection()
    conn.cursor().executemany("UPDATE users SET badge=? WHERE name=?", users_to_update)
    conn.commit()
    conn.close()

def update_assessment_score(name, lang, score):
    """Updates the assessment score for a specific language for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT assessment_scores FROM users WHERE name=?", (name,))
    scores_str = cursor.fetchone()['assessment_scores']
    scores = json.loads(scores_str or '{}')
    scores[lang] = score
    cursor.execute("UPDATE users SET assessment_scores=? WHERE name=?", (json.dumps(scores), name))
    conn.commit()
    conn.close()

def update_resume_text(name, text):
    """Saves the user's resume text to the database."""
    conn = get_db_connection()
    conn.cursor().execute("UPDATE users SET resume_text=? WHERE name=?", (text, name))
    conn.commit()
    conn.close()

def get_leaderboard_data():
    """Fetches the top 10 users for the leaderboard, ordered by gems."""
    conn = get_db_connection()
    users = conn.cursor().execute("SELECT name, skill, gems, badge FROM users ORDER BY gems DESC LIMIT 10").fetchall()
    conn.close()
    return users
