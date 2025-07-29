# agents.py
# This file contains the core logic for all the platform's features (the "agents").

import time
import requests
import json
import getpass
import subprocess
import sys
import os
import random
import tempfile # BUG FIX: Re-added missing import

# Import from our other project files
from config import Colors
import database

# --- File Reading Helpers ---
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

def read_pdf_text(file_path):
    if not PyPDF2:
        print(f"{Colors.FAIL}PyPDF2 library is required to read PDF files. Run 'pip install PyPDF2'{Colors.ENDC}")
        return None
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

def read_docx_text(file_path):
    if not docx:
        print(f"{Colors.FAIL}python-docx library is required to read DOCX files. Run 'pip install python-docx'{Colors.ENDC}")
        return None
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


# --- Generative AI Function ---
def call_gemini_api(prompt, is_json_response=False, retries=3):
    """A robust helper function to call the Gemini API with automatic retries."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"\n{Colors.FAIL}ERROR: GEMINI_API_KEY environment variable not set.{Colors.ENDC}")
        return None

    print(f"\n{Colors.CYAN}Maverick is thinking...{Colors.ENDC}")
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    if is_json_response:
        payload["generationConfig"] = {"temperature": 0.7, "responseMimeType": "application/json"}
    else:
        payload["generationConfig"] = {"temperature": 1.0}

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    for attempt in range(retries):
        try:
            res = requests.post(api_url, headers=headers, json=payload, timeout=20)
            res.raise_for_status()
            part = res.json()['candidates'][0]['content']['parts'][0]
            return part.get('text', 'Could not parse AI response.')
        except requests.exceptions.HTTPError as e:
            if 500 <= e.response.status_code < 600 and attempt < retries - 1:
                print(f"{Colors.WARNING}Server error ({e.response.status_code}) detected. Retrying in {2 ** attempt} seconds...{Colors.ENDC}")
                time.sleep(2 ** attempt)
                continue
            else:
                print(f"{Colors.FAIL}An HTTP error occurred with the AI API: {e}{Colors.ENDC}")
                return None
        except Exception as e:
            print(f"{Colors.FAIL}An unexpected error occurred with the AI API: {e}{Colors.ENDC}")
            return None
    
    print(f"{Colors.FAIL}AI service is still unavailable after {retries} attempts.{Colors.ENDC}")
    return None

# --- Agent Implementations ---

# 1. Profile Agent
def update_profile_from_resume(current_user):
    print(f"\n{Colors.HEADER}--- 📄 Update Profile from Resume ---{Colors.ENDC}")
    file_path = input("Enter the full path to your resume file (.txt, .pdf, .docx): ").strip().strip('"')
    
    resume_text = None
    try:
        if file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f: resume_text = f.read()
        elif file_path.lower().endswith('.pdf'):
            resume_text = read_pdf_text(file_path)
        elif file_path.lower().endswith('.docx'):
            resume_text = read_docx_text(file_path)
        else:
            print(f"{Colors.FAIL}Unsupported file type.{Colors.ENDC}")
            return

        if not resume_text:
            print(f"{Colors.WARNING}Could not read text from the resume.{Colors.ENDC}")
            return

        database.update_resume_text(current_user['name'], resume_text)

        skill_prompt = f"Analyze the following resume and extract the top 5 technical skills. Return ONLY a comma-separated list.\n\nResume:\n{resume_text}"
        extracted_skills = call_gemini_api(skill_prompt)

        if extracted_skills:
            print(f"\n{Colors.GREEN}✅ Resume updated!{Colors.ENDC}")
            print(f"{Colors.CYAN}Maverick identified these key skills:{Colors.ENDC} {extracted_skills}")
            
            job_prompt = f'Based on this resume, suggest 3 relevant job titles and a percentage match for each. Return ONLY a valid JSON object like {{"Software Engineer": "90%"}}.\n\nResume:\n{resume_text}'
            job_suggestions_json = call_gemini_api(job_prompt, is_json_response=True)
            
            if job_suggestions_json:
                try:
                    suggestions = json.loads(job_suggestions_json)
                    print(f"\n{Colors.HEADER}--- 🎯 AI Job Role Suggestions ---{Colors.ENDC}")
                    print(f"{Colors.BOLD}{'Suggested Role':<25}{'Your Match'}{Colors.ENDC}")
                    print("-" * 40)
                    for role, match in suggestions.items():
                        print(f"{role:<25}{Colors.GREEN}{match}{Colors.ENDC}")
                except json.JSONDecodeError:
                    print(f"{Colors.WARNING}Could not parse job suggestions.{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}Could not analyze the resume.{Colors.ENDC}")

    except FileNotFoundError:
        print(f"{Colors.FAIL}Error: File not found.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}An error occurred: {e}{Colors.ENDC}")

# 2. Assessment Agent
def take_ai_assessment(current_user):
    print(f"\n{Colors.HEADER}--- 📝 AI-Powered Skill Assessment ---{Colors.ENDC}")
    lang = input("Which language to assess (python/java/c++)? ").strip().lower()
    if lang not in ('python', 'java', 'c++'):
        print(f"{Colors.FAIL}Invalid language.{Colors.ENDC}")
        return

    # Part 1: MCQ
    print(f"\n{Colors.BOLD}Part 1: Multiple Choice Questions{Colors.ENDC}")
    prompt_mcq = f"Generate a 3-question multiple-choice quiz on basic {lang}. MUST return ONLY a valid JSON array of objects with keys: 'question', 'options' (dict with 'a','b','c'), and 'answer'."
    quiz_json_string = call_gemini_api(prompt_mcq, is_json_response=True)
    if not quiz_json_string: return

    quiz_score = 0
    try:
        quiz = json.loads(quiz_json_string)
        for i, item in enumerate(quiz, 1):
            print(f"\n{Colors.BOLD}Q{i}: {item['question']}{Colors.ENDC}")
            for key, value in item['options'].items(): print(f"  {key}) {value}")
            user_answer = input("Your answer: ").lower()
            if user_answer == item['answer']:
                print(f"{Colors.GREEN}Correct!{Colors.ENDC}")
                quiz_score += 1
            else:
                correct_key = item['answer']
                correct_value = item['options'][correct_key]
                print(f"{Colors.FAIL}Incorrect. The correct answer was: {correct_key}) {correct_value}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}AI returned an invalid quiz format. Error: {e}{Colors.ENDC}")
        return

    # Part 2: Coding Challenge
    print(f"\n{Colors.BOLD}Part 2: Live Coding Challenge{Colors.ENDC}")
    prompt_coding = f"Generate a beginner {lang} coding challenge. MUST return ONLY a valid JSON object with keys: 'problem', 'check_code', and 'expected_output'."
    challenge_json_string = call_gemini_api(prompt_coding, is_json_response=True)
    if not challenge_json_string: return

    coding_score = 0
    try:
        challenge = json.loads(challenge_json_string)
        print(f"\n{Colors.WARNING}Your task:{Colors.ENDC} {challenge['problem']}")
        print("Enter your code solution (end with blank line):")
        lines = [line for line in iter(input, '')]
        user_code = '\n'.join(lines)

        if user_code:
            error, output = execute_code(user_code, language=lang, check_code=challenge.get('check_code', ''), current_user=current_user)
            expected = challenge.get('expected_output', '')
            if not error and output is not None and output.strip() == expected.strip():
                print(f"{Colors.GREEN}Coding challenge passed!{Colors.ENDC}")
                coding_score = 1
            else:
                print(f"{Colors.FAIL}Coding challenge failed. Expected '{expected}', but got '{output.strip() if output else 'No output'}'.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}AI returned an invalid challenge format. Error: {e}{Colors.ENDC}")
        return

    final_score = ((quiz_score / 3 * 0.5) + (coding_score * 0.5)) * 100
    print(f"\n{Colors.GREEN}Assessment Complete! Your final score for {lang.capitalize()}: {final_score:.0f}%{Colors.ENDC}")
    database.update_assessment_score(current_user['name'], lang, final_score)

# 3. Recommender Agent (Integrated into other agents)
def debug_with_ai(code, error_message):
    prompt = f"Act as an expert code debugger. A user's code is failing.\n\nCode:\n```{code}```\nError:\n```{error_message}```\nProvide a structured explanation with headers: THE BUG, THE FIX, EXPLANATION."
    debug_advice = call_gemini_api(prompt)
    if not debug_advice: return
        
    print(f"\n{Colors.CYAN}--- 🤖 AI Debugging Analysis ---{Colors.ENDC}")
    for header in ["THE BUG:", "THE FIX:", "EXPLANATION:"]:
         debug_advice = debug_advice.replace(header, f"\n{Colors.BOLD}{Colors.FAIL if header == 'THE BUG:' else Colors.GREEN if header == 'THE FIX:' else Colors.CYAN}{header.replace(':', '')}:{Colors.ENDC}")
    print(debug_advice)
    print(f"{Colors.CYAN}{'-' * 30}{Colors.ENDC}")

def explain_concept_cli():
    concept = input("Enter concept to explain: ").strip()
    if not concept:
        print(f"{Colors.WARNING}No input received.{Colors.ENDC}")
        return

    prompt = f"""
    Explain the programming concept '{concept}'. Use a creative analogy.
    If the concept involves a sequence of steps or decisions (like a loop or if-statement), you MUST include a simple text-based, diagrammatic flowchart (ASCII art) using characters like ->, |, <>, [], and ().
    Structure your response with the following exact headers on new lines:
    CONCEPT:
    ANALOGY:
    KEY POINTS:
    - Point 1
    - Point 2
    DIAGRAM: (Only if applicable)
    """
    
    explanation = call_gemini_api(prompt)
    if not explanation:
        print(f"{Colors.FAIL}Could not get an explanation from the AI.{Colors.ENDC}")
        return

    print(f"\n{Colors.HEADER}--- 🧠 AI Explanation for '{concept.capitalize()}' ---{Colors.ENDC}")
    
    lines = explanation.strip().split('\n')
    for line in lines:
        if line.startswith("CONCEPT:"):
            print(f"\n{Colors.BOLD}{Colors.CYAN}Concept:{Colors.ENDC}{line.replace('CONCEPT:', '').strip()}")
        elif line.startswith("ANALOGY:"):
            print(f"\n{Colors.BOLD}{Colors.CYAN}Analogy:{Colors.ENDC}{line.replace('ANALOGY:', '').strip()}")
        elif line.startswith("KEY POINTS:"):
            print(f"\n{Colors.BOLD}{Colors.CYAN}Key Points:{Colors.ENDC}")
        elif line.strip().startswith("-"):
            print(f"  {Colors.GREEN}•{Colors.ENDC} {line.strip().lstrip('-').strip()}")
        elif line.startswith("DIAGRAM:"):
            print(f"\n{Colors.BOLD}{Colors.CYAN}Diagram:{Colors.ENDC}")
        else:
            print(f"  {line}")
    print(f"{Colors.HEADER}{'-' * 50}{Colors.ENDC}")

# 4. Learning Management Tracker Agent
def show_dashboard(current_user):
    print(f"\n{Colors.HEADER}=== 📊 Personal Dashboard ==={Colors.ENDC}")
    print(f"{Colors.BOLD}{'Attribute':<25}{'Value'}{Colors.ENDC}")
    print("-" * 40)
    print(f"{'User:':<25}{current_user['name']}")
    print(f"{'Primary Skill:':<25}{current_user['skill']}")
    print(f"{'Badge:':<25}{current_user['badge']}")
    print(f"{'Gems 💎:':<25}{current_user['gems']}")
    print(f"{'🔥 Streak:':<25}{current_user.get('streak', 0)} days")
    
    progress, _ = calculate_progress_to_next_badge(current_user['gems'])
    bar = ('★' * (progress // 10)).ljust(10)
    print(f"{'Progress to next badge:':<25}[{Colors.GREEN}{bar}{Colors.ENDC}] {progress}%")
    
    summary_prompt = f"User has {current_user['gems']} gems, badge {current_user['badge']}, skill {current_user['skill']}. Give a short motivational summary."
    summary = call_gemini_api(summary_prompt)
    print(f"\n{Colors.CYAN}🤖 AI Summary:{Colors.ENDC}")
    print(summary)

def show_leaderboard():
    """Updates all user badges before displaying the leaderboard."""
    print(f"\n{Colors.HEADER}--- 🏆 Syncing Badges ---{Colors.ENDC}")
    all_users = database.get_all_users()
    updates = []
    for user in all_users:
        new_badge = calculate_badge(user['gems'])
        if new_badge != user['badge']:
            updates.append((new_badge, user['name']))
    
    if updates:
        database.batch_update_badges(updates)
        print(f"{Colors.GREEN}Leaderboard badges have been updated!{Colors.ENDC}")

    print(f"\n{Colors.HEADER}=== 🏆 Global Leaderboard ==={Colors.ENDC}")
    users_for_display = database.get_leaderboard_data()
    print(f"{Colors.BOLD}{'Rank':<6}{'Name':<15}{'Skill':<10}{'Gems 💎':<10}{'Badge':<20}{Colors.ENDC}")
    print("-" * 61)
    for i, user_row in enumerate(users_for_display, 1):
        user = dict(user_row)
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f" {i}."
        print(f"{medal:<6}{user['name']:<15}{user['skill']:<10}{user['gems']:<10}{user['badge']:<20}")
    
    if users_for_display:
        top_user_name = dict(users_for_display[0])['name']
        praise_prompt = f"Give a cool 1-liner praise for coder '{top_user_name}' who topped the leaderboard."
        comment = call_gemini_api(praise_prompt)
        print(f"\n{Colors.CYAN}👑 AI Praise for {top_user_name}: {comment}{Colors.ENDC}")


# 5. Hackathon Agent
def hackathon_portal():
    print(f"\n{Colors.HEADER}--- 🏆 Hackathon Portal ---{Colors.ENDC}")
    print("1. Join 'AI for Good' Hackathon")
    print("2. ✨ Generate a new Hackathon idea with AI")
    print("3. Return to Main Menu")
    choice = input("Choice: ")
    if choice == '1':
        print(f"\n{Colors.GREEN}✅ You have joined the 'AI for Good' Hackathon!{Colors.ENDC}")
    elif choice == '2':
        topic = input("What topic are you interested in? (e.g., 'healthcare', 'gaming'): ")
        prompt = f"Generate a single, creative hackathon challenge idea related to '{topic}'. Include a catchy name and a one-sentence problem statement."
        idea = call_gemini_api(prompt)
        print(f"\n{Colors.CYAN}--- AI-Generated Hackathon Idea ---\n{idea}{Colors.ENDC}")

# --- Other Helper Functions ---
def execute_code(code, language='python', check_code=None, current_user=None):
    """BUG FIX: This version correctly handles execution and output for all languages."""
    start = time.time()
    error, output = None, ""
    full_code = code + (f"\n{check_code}" if check_code else "")

    try:
        if language == 'python':
            result = subprocess.run([sys.executable, '-c', full_code], capture_output=True, text=True, timeout=5)
            if result.returncode != 0: raise Exception(result.stderr)
            output = result.stdout
        elif language == 'java':
            with tempfile.TemporaryDirectory() as tmpdir:
                path = os.path.join(tmpdir, 'Main.java')
                with open(path, 'w') as f: f.write(code)
                cp = subprocess.run(['javac', path], capture_output=True, text=True, timeout=10)
                if cp.returncode: raise Exception(cp.stderr)
                rp = subprocess.run(['java', '-cp', tmpdir, 'Main'], capture_output=True, text=True, timeout=5)
                if rp.returncode: raise Exception(rp.stderr)
                output = rp.stdout
        elif language == 'c++':
            with tempfile.TemporaryDirectory() as tmpdir:
                src = os.path.join(tmpdir, 'main.cpp')
                exe = os.path.join(tmpdir, 'main.exe' if os.name == 'nt' else 'a.out')
                with open(src, 'w') as f: f.write(code)
                cp = subprocess.run(['g++', src, '-o', exe], capture_output=True, text=True, timeout=10)
                if cp.returncode: raise Exception(cp.stderr)
                rp = subprocess.run([exe], capture_output=True, text=True, timeout=5)
                if rp.returncode: raise Exception(rp.stderr)
                output = rp.stdout
    except Exception as e:
        error = str(e)
    
    elapsed = time.time() - start

    if error:
        print(f"{Colors.FAIL}Error: {error.strip()}{Colors.ENDC}")
    else:
        if not check_code:
            print(f"{Colors.GREEN}Output: {output.strip()}{Colors.ENDC}")

    if not check_code:
        if not error:
            gems_earned = random.randint(1, 5)
            database.update_user_gems(current_user['name'], gems_earned)
            print(f"{Colors.GREEN}Success! You earned {gems_earned} 💎 gems.{Colors.ENDC}")
        
        print(f"Time: {elapsed:.4f}s")
        provide_ai_feedback(code, error, elapsed)
            
    return error, output

# BUG FIX: Re-added the missing provide_ai_feedback function
def provide_ai_feedback(code, error, elapsed):
    prompt = f"Act as a coding mentor. Here's a user's code:\n\n{code}\n\nIt {'had an error: ' + error if error else 'ran successfully'} in {elapsed:.2f} seconds. Give one-line:\n- Compliment\n- Performance comment\n- Area of improvement (if any)"
    feedback = call_gemini_api(prompt)
    print(f"\n{Colors.CYAN}🤖 AI Feedback:{Colors.ENDC}")
    print(feedback)

def calculate_badge(gems):
    """Helper function with expanded badge tiers."""
    if gems >= 500: return 'Maverick Master 🏆'
    if gems >= 250: return 'Logic Legend 🧙'
    if gems >= 100: return 'Syntax Slayer ⚔️'
    if gems >= 50: return 'Code Crafter 🎨'
    if gems >= 10: return 'Apprentice 🛠️'
    return 'Newbie 🔰'

def calculate_progress_to_next_badge(gems):
    """Calculates the percentage progress to the next badge."""
    if gems < 10: return int((gems / 10) * 100), 'Apprentice'
    if gems < 50: return int(((gems - 10) / 40) * 100), 'Code Crafter'
    if gems < 100: return int(((gems - 50) / 50) * 100), 'Syntax Slayer'
    if gems < 250: return int(((gems - 100) / 150) * 100), 'Logic Legend'
    if gems < 500: return int(((gems - 250) / 250) * 100), 'Maverick Master'
    return 100, 'Max Level'


def check_and_award_badge(current_user):
    """More intelligent badge system that only announces promotions for the current user."""
    current_badge = current_user['badge']
    gems = current_user['gems']
    new_badge = calculate_badge(gems)
    
    if new_badge != current_badge:
        database.update_user_badge(current_user['name'], new_badge)
        print(f"\n{Colors.GREEN}🎉 Badge Promotion! You are now a {new_badge}!{Colors.ENDC}")
        return new_badge
    return current_badge
