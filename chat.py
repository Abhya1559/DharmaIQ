from flask import Flask, request, jsonify
import sqlite3
import os
from google import genai
from dotenv import load_dotenv
import time
import re
from rapidfuzz import process, fuzz

# Load environment variables
load_dotenv()
print("✅ Environment Loaded")

# Initialize Flask
app = Flask(__name__)

# Google Gemini AI Client
client = genai.Client(api_key=os.environ['API_KEY'])

DB_FILE = "movie_dialogues.db"

def clean_text(text):
    """Removes unwanted characters and formatting from dialogues."""
    text = re.sub(r"\s+", " ", text)  # Replace multiple spaces/newlines with a single space
    text = text.strip()  # Trim leading/trailing spaces
    return text

def fetch_dialogue(character, user_message):
    """Fetches the closest matching dialogue for the character from SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Try to find an **exact** dialogue match first
    cursor.execute("""
        SELECT dialogues FROM movie_dialogues
        WHERE character_name = ? AND dialogues LIKE ?
        ORDER BY LENGTH(dialogues) ASC
        LIMIT 1
    """, (character, f"% {user_message} %"))  # Space-padding ensures better matching

    result = cursor.fetchone()

    # If exact match found, return it
    if result:
        conn.close()
        return clean_text(result[0])

    # If no exact match, perform fuzzy search
    cursor.execute("SELECT dialogues FROM movie_dialogues WHERE character_name = ?", (character,))
    all_dialogues = [row[0] for row in cursor.fetchall()]
    conn.close()

    if all_dialogues:
        # Use fuzzy matching to find the best match
        best_match, score, _ = process.extractOne(user_message, all_dialogues, scorer=fuzz.partial_ratio)

        # If match confidence is high enough, return it
        if score > 80:
            return clean_text(best_match)

    return None  # No suitable match found

def generate_gemini_response(character, user_message):
    """Generates a realistic response using Gemini AI if no exact or close match is found."""
    print(f"⚡ No match found for '{user_message}'. Using Gemini AI...")

    prompt = f"""
    Act exactly like {character} from the movie script. 
    Stay in character and respond naturally, as if you were in the scene. 
    Given this line from another character: "{user_message}", 
    how would {character} realistically reply based on their personality and speaking style?
    """

    try:
        gemini_api_response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        return gemini_api_response.text
    except Exception as e:
        print(f"❌ Error with Gemini API: {e}")
        return "Sorry, I couldn't generate a response."

@app.route("/chat", methods=["POST"])
def chat():
    """Handles character-based dialogue lookup and AI response."""
    data = request.json
    character = data.get("character")
    user_message = data.get("user_message")

    if not character or not user_message:
        return jsonify({"error": "Missing required fields"}), 400

    start_time = time.time()

    # Check SQLite for stored dialogue
    response = fetch_dialogue(character, user_message)

    if not response:
        # Use Gemini AI if no exact or close match found
        response = generate_gemini_response(character, user_message)

    end_time = time.time()
    print(f"Response Time: {round((end_time - start_time) * 1000, 2)}ms")

    return jsonify({"character": character, "response": response})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
