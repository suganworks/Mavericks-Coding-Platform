# db_manager.py
# A simple tool to manage the users in your mavericks.db database.

import sqlite3

DB_FILE = "mavericks.db"

def get_db_connection():
    """Establishes and returns a connection to the database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def list_all_users():
    """Fetches and prints all users from the database."""
    conn = get_db_connection()
    users = conn.cursor().execute("SELECT id, name, gems, badge FROM users ORDER BY name").fetchall()
    conn.close()
    
    print("\n--- Current Users in Database ---")
    if not users:
        print("The database is currently empty.")
        return

    print(f"{'ID':<5}{'Name':<20}{'Gems':<10}{'Badge'}")
    print("-" * 45)
    for user in users:
        print(f"{user['id']:<5}{user['name']:<20}{user['gems']:<10}{user['badge']}")
    print("-" * 45)

def delete_user_by_name():
    """Deletes a specific user from the database by their name."""
    list_all_users()
    name_to_delete = input("\nEnter the exact name of the user you want to delete: ").strip()

    if not name_to_delete:
        print("No name entered.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, check if the user exists
    cursor.execute("SELECT * FROM users WHERE name=?", (name_to_delete,))
    user = cursor.fetchone()
    
    if user:
        # If the user exists, proceed with deletion
        cursor.execute("DELETE FROM users WHERE name=?", (name_to_delete,))
        conn.commit()
        print(f"\nSuccessfully deleted user '{name_to_delete}'.")
    else:
        print(f"\nUser '{name_to_delete}' not found.")
        
    conn.close()

def main_menu():
    """Displays the main menu and handles user input."""
    while True:
        print("\n--- Mavericks Database Manager ---")
        print("1. List All Users")
        print("2. Delete a User by Name")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            list_all_users()
        elif choice == '2':
            delete_user_by_name()
        elif choice == '3':
            print("Exiting database manager.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
