import requests
import os
import csv
import re
import json
import time
from bs4 import BeautifulSoup
from pymongo import MongoClient
from joblib import Parallel, delayed
from tqdm import tqdm
from tqdm_joblib import tqdm_joblib  
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
print("✅ Environment Loaded")

# Configure Gemini API
genai.configure(api_key=os.getenv("API_KEY"))

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Movie"
COLLECTION_NAME = "scripts"
CLEANED_COLLECTION = "cleaned_scripts"

# Parallel processing
NUM_WORKERS = 16  # Adjust based on CPU cores

# Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
cleaned_collection = db[CLEANED_COLLECTION]

# --------------------------- SCRAPE MOVIE SCRIPTS ---------------------------
def scrape_script(title, script_url):
    """Scrapes an individual script and saves it to MongoDB."""
    try:
        response = requests.get(script_url, timeout=10)
        if response.status_code != 200:
            return f" Failed: {title}"

        soup = BeautifulSoup(response.text, "html.parser")
        script_content = soup.find("pre")

        if script_content:
            script_text = script_content.get_text()
            collection.insert_one({"title": title, "script_url": script_url, "script_text": script_text})
            return f" Saved to MongoDB: {title}"
        else:
            return f" Not Found: {title}"

    except requests.exceptions.RequestException as e:
        return f"Error: {title} - {str(e)}"

def process_csv(filename="index.csv"):
    """Reads movie titles and script links from CSV and scrapes scripts in parallel."""
    if not os.path.exists(filename):
        print(f"Error: CSV file '{filename}' not found!")
        return

    with open(filename, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)  # Skip header row
        movies = [(title, script_url) for title, script_url in reader]

    if not movies:
        print("Error: CSV file is empty!")
        return

    with tqdm_joblib(tqdm(desc="Scraping Scripts", total=len(movies), ncols=100)):
        results = Parallel(n_jobs=NUM_WORKERS, backend="threading")(
            delayed(scrape_script)(title, script_url) for title, script_url in movies
        )

    for res in results:
        print(res)

# --------------------------- PROCESS AND CLEAN SCRIPTS ---------------------------
def clean_text(text):
    """Removes whitespace and special characters."""
    text = text.strip()
    text = re.sub(r"[^a-zA-Z0-9\s.,!?]", "", text)  # Keep basic punctuation
    return text

def extract_b_tags():
    """Extracts <b> tags (character names), cleans data, and stores processed dialogues."""
    scripts = list(collection.find({}, {"_id": 0, "title": 1, "script_text": 1}))
    b_contents = {}

    for script in scripts:
        title = script["title"]
        script_text = script["script_text"]
        soup = BeautifulSoup(script_text, "html.parser")

        # Extract character names from <b> tags
        b_tags = soup.find_all("b")
        b_contents[title] = list(set(clean_text(b.get_text()) for b in b_tags))

    return b_contents

# --------------------------- VALIDATE CHARACTERS USING GEMINI ---------------------------
def get_movie_characters(movie_name, character_list, retries=3):
    """Queries Google Gemini API to filter valid movie characters with error handling."""
    model = genai.GenerativeModel("gemini-pro")  

    prompt = f"""
    This is the movie "{movie_name}". I want you to return a JSON that contains only the valid character names from this list: {list(character_list)}.
    """

    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)

            if not response or not response.text:
                raise ValueError("Empty response from API")

            return json.loads(response.text)  # Convert response to JSON

        except json.JSONDecodeError:
            print(f" JSON Parsing Error for {movie_name}. Retrying ({attempt+1}/{retries})...")
            time.sleep(2)  # Avoid spamming the API
        except Exception as e:
            print(f" API Error for {movie_name}: {e}. Retrying ({attempt+1}/{retries})...")
            time.sleep(5)  # Avoid rate limits

    print(f" Skipping {movie_name} due to repeated API failures.")
    return list(character_list)  # Return original list if API fails

# --------------------------- STORE CLEANED DATA IN MONGODB ---------------------------
def store_cleaned_data():
    """Processes and stores cleaned movie dialogues in MongoDB."""
    b_cleaned = extract_b_tags()

    # Reduce API calls: Only query for movies with characters extracted
    characters_final = {}
    for title, characters in tqdm(b_cleaned.items(), desc="Processing Movies", ncols=100):
        if characters:
            characters_final[title] = get_movie_characters(title, set(characters))

    for title, characters in characters_final.items():
        cleaned_collection.insert_one({
            "title": title,
            "characters": characters
        })

    print("Cleaned data stored in MongoDB!")

# --------------------------- MAIN FUNCTION ---------------------------
if __name__ == "__main__":
    process_csv("index.csv")  # Scrape scripts (if not already done)
    store_cleaned_data()  # Process & store cleaned dialogues
