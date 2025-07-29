# main.py
# This is the main entry point for the Mavericks Platform application.
# It connects all the other modules (agents, database, config) and runs the app.

import getpass
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# Import from our other project files
from config import Colors
import database
import agents

# --- Global State ---
# This dictionary will hold the data for the currently logged-in user
current_user = None

# --- Auth Functions (User Interface Layer) ---
def register():
    """Handles the user interface for registration."""
    print(f"\n{Colors.HEADER}--- Register ---{Colors.ENDC}")
    name = input("Choose username: ").strip()
    password = getpass.getpass("Choose password: ")
    skill = input("Primary skill (python/java/c++): ").strip().lower()
    
    if database.create_user(name, password, skill):
        print(f"{Colors.GREEN}✅ User '{name}' registered successfully. Please log in.{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}❌ Username already exists.{Colors.ENDC}")

def login():
    """Handles the user interface for logging in."""
    global current_user
    print(f"\n{Colors.HEADER}--- Login ---{Colors.ENDC}")
    name = input("Name: ").strip()
    password = getpass.getpass("Password: ")
    
    user_data = database.get_user_by_credentials(name, password)
    
    if user_data:
        current_user = user_data
        database.update_login_streak(name)
        
        # Check for badge promotion on login
        new_badge = agents.check_and_award_badge(current_user)
        if new_badge != current_user['badge']:
            # If a new badge was awarded, refresh the user data
            current_user = database.get_user_by_name(name)

        print(f"{Colors.GREEN}👋 Welcome back, {current_user['name']}!{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}❌ Invalid credentials.{Colors.ENDC}")

def logout():
    """Logs the current user out."""
    global current_user
    print(f"Goodbye, {current_user['name']}!")
    current_user = None

# --- Core Feature (Compiler) ---
def interactive_code_compiler():
    """Handles the user interface for the code compiler."""
    global current_user
    while True:
        lang = input("Language (python/java/c++), or 'back': ").strip().lower()
        if lang == 'back':
            break
        if lang not in ('python', 'java', 'c++'):
            print(f"{Colors.FAIL}Invalid language.{Colors.ENDC}")
            continue
            
        print("Enter your code (end with a blank line):")
        lines = [line for line in iter(input, '')]
        code = '\n'.join(lines)
        
        if code:
            error, _ = agents.execute_code(code, language=lang, current_user=current_user)
            if error:
                choice = input(f"\n{Colors.WARNING}An error occurred. Would you like Maverick to help you debug? (y/n): {Colors.ENDC}").lower()
                if choice == 'y':
                    agents.debug_with_ai(code, error)
            else:
                # Refresh user data to get the new gem count
                current_user = database.get_user_by_name(current_user['name'])
                # Check for a promotion
                new_badge = agents.check_and_award_badge(current_user)
                if new_badge != current_user['badge']:
                    current_user['badge'] = new_badge # Update local data
            
            # Refresh user data again after potential badge change
            current_user = database.get_user_by_name(current_user['name'])


# --- Menu Display Functions ---
def show_auth_menu():
    print(f"\n{Colors.HEADER}=== Mavericks Platform ==={Colors.ENDC}")
    print("1. Login")
    print("2. Register")
    print("3. Exit")

def show_user_menu():
    print(f"\n{Colors.HEADER}=== Welcome {current_user['name']} ==={Colors.ENDC}")
    print(f"{Colors.BOLD}1. 💻 Run Code (Compiler){Colors.ENDC}")
    print(f"{Colors.BOLD}2. 📝 Take AI Skill Assessment{Colors.ENDC}")
    print(f"{Colors.BOLD}3. 🏆 Enter Hackathon Portal{Colors.ENDC}")
    print(f"{Colors.BOLD}4. 🧠 Explain a Concept with AI{Colors.ENDC}")
    print(f"{Colors.BOLD}5. 📄 Update Profile from Resume{Colors.ENDC}")
    print(f"{Colors.BOLD}6. 📊 View Your Dashboard{Colors.ENDC}")
    print(f"{Colors.BOLD}7. 🥇 View Global Leaderboard{Colors.ENDC}")
    print(f"{Colors.BOLD}8. 🚪 Logout{Colors.ENDC}")

# --- Main Application Loop ---
def main_loop():
    """The main function that runs the application loop."""
    global current_user
    database.setup_database() # Ensure tables exist before we start
    
    while True:
        if current_user:
            show_user_menu()
            choice = input("Choice: ")
            if choice == '1':
                interactive_code_compiler()
            elif choice == '2':
                agents.take_ai_assessment(current_user)
            elif choice == '3':
                agents.hackathon_portal()
            elif choice == '4':
                agents.explain_concept_cli()
            elif choice == '5':
                agents.update_profile_from_resume(current_user)
            elif choice == '6':
                agents.show_dashboard(current_user)
            elif choice == '7':
                agents.show_leaderboard()
            elif choice == '8':
                logout()
        else:
            show_auth_menu()
            choice = input("Choice: ")
            if choice == '1':
                login()
            elif choice == '2':
                register()
            elif choice == '3':
                print("Thank you for using the Mavericks Platform!")
                break

if __name__ == '__main__':
    # This ensures the main_loop function runs when the script is executed
    main_loop()
