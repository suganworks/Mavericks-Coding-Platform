# update_scores.py
# This is a one-time use script to populate your mavericks.db with random,
# realistic user data for a more impressive demonstration leaderboard.

import sqlite3
import random

# --- Configuration ---
# A list of random Indian names to populate the leaderboard
indian_names = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Saanvi", "Aadhya", "Kiara", "Diya", "Pari", "Ananya",
    "Riya", "Sitara", "Dhruv", "Kabir", "Rohan", "Priya", "Sameer", "Neha", "Vikram"
]

# The skills that will be randomly assigned to the users
skills = ["python", "java", "c++"]

# --- Database Connection ---
try:
    # Connect to the database file in the same folder
    conn = sqlite3.connect("mavericks.db")
    cursor = conn.cursor()

    print("Connected to the database. Populating with random user data...")

    # Loop through the names and create/update users with random data
    for name in indian_names:
        # Assign a random skill
        random_skill = random.choice(skills)
        # NEW: Assign a more realistic random number of gems for a better leaderboard
        random_gems = random.randint(1, 150)
        # Simple password for these demo accounts
        password = "123"

        try:
            # Try to insert a new user. If the user already exists, this will fail.
            cursor.execute(
                "INSERT INTO users (name, password, skill, gems, assessment_scores) VALUES (?, ?, ?, ?, ?)",
                (name, password, random_skill, random_gems, '{}')
            )
            print(f" - Created new user '{name}' with {random_gems} gems.")
        except sqlite3.IntegrityError:
            # If the user already exists, just update their gems.
            cursor.execute("UPDATE users SET gems = ?, skill = ? WHERE name = ?", (random_gems, random_skill, name))
            print(f" - Updated existing user '{name}' to have {random_gems} gems.")

    # Save (commit) the changes to the database file
    conn.commit()
    print("\nSuccessfully populated the database with random leaderboard data!")

except sqlite3.Error as e:
    print(f"\nAn error occurred: {e}")

finally:
    # Always close the connection when you're done
    if conn:
        conn.close()
        print("Database connection closed.")
