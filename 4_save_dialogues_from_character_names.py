import os
import csv
import re
import sqlite3
from collections import defaultdict
from bs4 import BeautifulSoup

SCRIPT_FOLDER = "movie_scripts"
CHARACTER_CSV = "character_names.csv"
DB_FILE = "movie_dialogues.db"

def clean_dialogue(dialogue):
    """Removes unwanted tags, excessive spaces, and strange formatting."""
    dialogue = re.sub(r"</?b>", "", dialogue)  # Remove <b> tags
    dialogue = re.sub(r"\s+", " ", dialogue)  # Normalize spaces
    dialogue = dialogue.replace("\n", " ").strip()  # Remove newlines
    return dialogue

def extract_dialogues(script_file, character_names):
    """
    Extracts all dialogues for each character in a script file.
    Returns a dictionary {character: [list of dialogues]}.
    """
    dialogues = defaultdict(list)

    with open(script_file, "r", encoding="utf-8") as file:
        script_text = file.read()

    # Parse the script with BeautifulSoup to remove HTML-like tags
    soup = BeautifulSoup(script_text, "html.parser")
    cleaned_text = soup.get_text()

    # Regex pattern to match character dialogues
    dialogue_pattern = re.compile(r"\b(" + "|".join(re.escape(name) for name in character_names) + r")\b\s*(.*?)(?=\n\n|\n<b>|$)", re.DOTALL)

    # Find all matches
    matches = dialogue_pattern.findall(cleaned_text)

    for character, dialogue in matches:
        cleaned_dialogue = clean_dialogue(dialogue)
        if cleaned_dialogue:
            dialogues[character].append(cleaned_dialogue)

    return dialogues

def create_database():
    """Creates SQLite database and table if not exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movie_dialogues (
        script_name TEXT NOT NULL,
        character_name TEXT NOT NULL,
        dialogues TEXT NOT NULL,
        PRIMARY KEY (script_name, character_name)
    )
    """)
    
    conn.commit()
    conn.close()

def insert_into_database(script_name, character_name, dialogues):
    """Inserts or updates character dialogues into SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Convert list of dialogues into a single text entry
    dialogues_text = " | ".join(dialogues)

    cursor.execute("""
    INSERT INTO movie_dialogues (script_name, character_name, dialogues) 
    VALUES (?, ?, ?)
    ON CONFLICT(script_name, character_name) DO UPDATE SET dialogues=excluded.dialogues
    """, (script_name, character_name, dialogues_text))

    conn.commit()
    conn.close()

def process_scripts():
    """Reads character names from CSV, extracts dialogues from scripts, and stores results in SQLite DB."""
    create_database()

    # Read character names from CSV
    with open(CHARACTER_CSV, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row

        for row in reader:
            script_name, character_list = row
            character_names = character_list.split(", ")

            script_file = os.path.join(SCRIPT_FOLDER, script_name)
            if os.path.exists(script_file):
                print(f"Processing {script_name}...")
                dialogues = extract_dialogues(script_file, character_names)

                # Insert into database
                for character, dialogue_list in dialogues.items():
                    insert_into_database(script_name, character, dialogue_list)
            else:
                print(f"Script file {script_name} not found.")

def search_dialogue(keyword):
    """Searches for a keyword in dialogues across all scripts and characters."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    keyword = f"%{keyword}%"  # Prepare for SQL LIKE query
    cursor.execute("""
    SELECT script_name, character_name, dialogues 
    FROM movie_dialogues 
    WHERE dialogues LIKE ?
    """, (keyword,))

    results = cursor.fetchall()
    conn.close()

    return results

if __name__ == "__main__":
    process_scripts()

    # Example: Search for dialogues containing a specific word
    search_word = "truth"
    print(f"\n🔎 Searching for dialogues containing '{search_word}':\n")
    results = search_dialogue(search_word)

    for script, character, dialogues in results:
        print(f"\n🎬 Script: {script}")
        print(f"🗣️ Character: {character}")
        print(f"💬 Dialogues: {dialogues[:300]}...")  # Print only first 300 characters
