# 🚀 Mavericks Coding Platform - Phase 1 Prototype

Welcome to the official repository for the **Mavericks Coding Platform**, a comprehensive, AI-powered developer growth engine designed to automate skill assessment, provide personalized learning, and gamify engagement. This Phase 1 prototype simulates all core features of the platform via a powerful console application.

---

## 🌟 Overview

The Mavericks Coding Platform is a Python-based, agent-driven simulation of a developer platform that uses **Google Gemini AI** to:

- Analyze resumes and recommend job roles
- Generate live coding assessments
- Explain complex programming concepts with analogies and flowcharts
- Track progress through a gamified dashboard
- Organize hackathons and brainstorm new ideas

---

## ✨ Core Features

### 🤖 Agent-Based Architecture

- **Profile Agent:** Extracts skills and job role matches from `.pdf`, `.docx`, or `.txt` resumes using AI.
- **Assessment Agent:** Conducts dynamic skill tests (MCQs + coding challenges) in Python, Java, and C++.
- **Recommender Agent:** Explains programming concepts and offers contextual debugging with AI.
- **Tracker Agent:** Tracks user progress, login streaks, badges, and gems in a persistent SQLite database.
- **Hackathon Agent:** Simulates joining hackathons and generates creative AI-powered hackathon ideas.

---

### 🖥️ Multi-Language Compiler

Built-in support for writing and executing code in:
- Python
- Java
- C++

All code execution and feedback are handled within the console.

---

### 💾 Data Persistence

User data is stored in a local SQLite file `mavericks.db`:
- Credentials
- Skills
- Resume text
- Assessment scores
- Gems and badges

---

### 🏆 Gamification

- **💎 Gems:** Earned for successful code execution and completing assessments
- **🎖️ Badges:** Unlock tiers: `Newbie 🔰`, `Apprentice 🛠️`, `Code Crafter 🎨`, `Syntax Slayer ⚔️`, `Logic Legend 🧙`, `Maverick Master 🏆`
- **🔥 Streaks:** Track daily login activity
- **Leaderboard:** Showcases top users with AI-generated praise
- **Motivational Dashboard:** Personal AI summary of progress

---

### 🔒 Clean, Secure & Modular Codebase

- **Modular Structure:**  
  Files include: `main.py`, `agents.py`, `database.py`, `config.py`, `update_scores.py`, `db_manager.py`
- **Environment Variables:**  
  Uses `.env` and `python-dotenv` for managing Gemini API keys securely
- **Colorful Console Output:**  
  Enhanced CLI experience with colored outputs (Windows & Linux compatible)

---

## 🛠️ Tech Stack

- **Language:** Python 3.6+
- **Database:** SQLite
- **AI API:** Google Gemini (`gemini-1.5-flash`)
- **External Tools:** `javac`, `g++` (optional for Java/C++ support)

### 📦 Python Dependencies

- `requests`
- `python-dotenv`
- `PyPDF2`
- `python-docx`

Install all dependencies:

```bash
pip install requests python-dotenv PyPDF2 python-docx

In case of AI not working, get your own API key from google gemini
