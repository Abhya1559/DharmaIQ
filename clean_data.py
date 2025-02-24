import requests
import os
import csv
import re
import json
from bs4 import BeautifulSoup
from pymongo import MongoClient
from joblib import Parallel, delayed
from tqdm import tqdm
from tqdm_joblib import tqdm_joblib
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load environment variables
load_dotenv()
print("✅ Environment Loaded")

# Configure Gemini API
genai.configure(api_key=os.getenv("API_KEY"))

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "MovieScriptsDB"
COLLECTION_NAME = "scripts"
CLEANED_COLLECTION = "cleaned_scripts"

# Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
cleaned_collection = db[CLEANED_COLLECTION]

def scrape_script(title, script_url):
    """Scrapes an individual script and saves it to MongoDB."""
    try:
        response = requests.get(script_url, timeout=10)
        if response.status_code != 200:
            return f"Failed: {title}"

        soup = BeautifulSoup(response.text, "html.parser")
        script_content = soup.find_all('pre')

        if script_content:
            script_text = script_content[0].get_text()
            collection.insert_one({"title": title, "script_url": script_url, "script_text": script_text})
            return f"Saved to MongoDB: {title}"
        else:
            return f"Not Found: {title}"
    except requests.exceptions.RequestException:
        return f"Error: {title}"

def extract_character_dialogues():
    """Extracts dialogues per character and stores them in MongoDB."""
    scripts = list(collection.find({}, {"_id": 0, "title": 1, "script_text": 1}))
    
    for script in scripts:
        title = script["title"]
        script_text = script["script_text"]
        soup = BeautifulSoup(script_text, "html.parser")
        
        dialogues = []
        character = None
        
        for line in soup.get_text().split("\n"):
            line = line.strip()
            if line.isupper() and len(line) < 30:  # Likely a character name
                character = line
            elif character and line:
                dialogues.append({"character": character, "dialogue": line})
        
        if dialogues:
            cleaned_collection.insert_one({"title": title, "dialogues": dialogues})
    
    print(" Dialogues stored in MongoDB!")

def find_matching_dialogue(movie_name, input_text):
    """Finds a closely matching dialogue from MongoDB."""
    movie = cleaned_collection.find_one({"title": movie_name}, {"_id": 0, "dialogues": 1})
    if not movie:
        return None
    
    dialogues = movie["dialogues"]
    
    for entry in dialogues:
        if input_text.lower() in entry["dialogue"].lower():
            return entry["dialogue"]
    
    return None

def generate_ai_response(movie_name, input_text):
    """Generates a response using Gemini AI if no matching dialogue is found."""
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"""
    You are a character in the movie "{movie_name}". Respond naturally to this dialogue: "{input_text}".
    """
    response = model.generate_content(prompt)
    return response.text.strip() if response else "I don't know."

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    movie_name = data.get("movie")
    input_text = data.get("message")
    
    if not movie_name or not input_text:
        return jsonify({"error": "Missing movie or message"}), 400
    
    response = find_matching_dialogue(movie_name, input_text)
    
    if response:
        return jsonify({"response": response})
    else:
        ai_response = generate_ai_response(movie_name, input_text)
        return jsonify({"response": ai_response})

if __name__ == "__main__":
    extract_character_dialogues()
    app.run(debug=True)
