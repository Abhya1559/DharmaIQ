import os
import csv
import requests
from google import genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re
import json
import time
from joblib import Parallel, delayed

load_dotenv()

SCRIPT_FOLDER = "movie_scripts"
OUTPUT_CSV = "character_names.csv"
API_KEYS = [os.environ["API_KEY_1"], os.environ["API_KEY_2"]]  # Use multiple API keys
MAX_RETRIES = 3  # Number of times to retry API requests on failure
RETRY_DELAY = 5  # Delay (in seconds) between retries
NUM_WORKERS = 2  # Number of parallel processes (adjust based on API keys)

# Create Gemini client instances BEFORE parallel processing
clients = {key: genai.Client(api_key=key) for key in API_KEYS}

def extract_bold_names(script_text):
    """Extracts unique names from <b> tags in the script."""
    soup = BeautifulSoup(script_text, "html.parser")
    bold_tags = soup.find_all("b")

    # Extract text, strip spaces, remove empty strings
    names = list(set(tag.get_text(strip=True) for tag in bold_tags if tag.get_text(strip=True)))

    return names

def clean_and_parse_json(text):
    """Cleans and parses JSON response from Gemini."""
    cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print("❌ Failed to parse JSON response.")
        return {}

def check_character_names(script_name, names, client):
    """Sends names to Gemini API to filter out character names, respecting rate limits."""
    prompt = f"""
    Hey Gemini! I am building a project that requires extracting character names from movie scripts.
    The script's filename is {script_name} and the character names are:
    {names}
    Return strictly in JSON format with the key being 'characters' and the value being the names of the characters in a list.
    DO NOT RETURN ANYTHING ELSE OTHER THAN THE CHARACTER NAMES. STRICTLY FOLLOW ALL MY INSTRUCTIONS.
    Please return only the names that belong to characters in the script. Exclude any non-character words.
    """

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            response = clean_and_parse_json(response.text)
            time.sleep(0.5)  # Ensure 2 requests per second
            return response.get("characters", [])
        except Exception as e:
            print(f"⚠️ API request failed for {script_name} (Attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                print(f"🔄 Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"❌ Max retries reached for {script_name}. Skipping.")
                return []  # Return empty list if all retries fail

def get_processed_scripts():
    """Reads the existing CSV file to determine which scripts have already been processed."""
    processed_scripts = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            processed_scripts = {row[0] for row in reader}  # Collect script names
    return processed_scripts

def process_script(filename, client):
    """Processes a single script: extracts names, validates with Gemini, and returns results."""
    try:
        filepath = os.path.join(SCRIPT_FOLDER, filename)
        print(f"📄 Processing: {filename}")

        # Read script text
        with open(filepath, "r", encoding="utf-8") as script_file:
            script_text = script_file.read()

        # Extract names from <b> tags
        extracted_names = extract_bold_names(script_text)

        # Validate character names using Gemini API
        character_names = check_character_names(filename, extracted_names, client)

        return [filename, ", ".join(character_names)]
    
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        return [filename, ""]

def process_scripts_parallel():
    """Processes all scripts in parallel and saves results to CSV."""
    processed_scripts = get_processed_scripts()
    all_files = sorted(os.listdir(SCRIPT_FOLDER))
    remaining_files = [f for f in all_files if f.endswith(".txt") and f not in processed_scripts]

    if not remaining_files:
        print("✅ All scripts have already been processed!")
        return

    print(f"Resuming from {remaining_files[0]}... ({len(remaining_files)} scripts left)")

    with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # If the file is new, add the header row
        if os.stat(OUTPUT_CSV).st_size == 0:
            writer.writerow(["Script Name", "Character Names"])

        # Assign clients to processes (round robin distribution)
        results = Parallel(n_jobs=NUM_WORKERS)(
            delayed(process_script)(filename, clients[API_KEYS[i % len(API_KEYS)]])
            for i, filename in enumerate(remaining_files)
        )

        # Save results immediately to CSV
        for result in results:
            writer.writerow(result)
            file.flush()  # Ensure data is written immediately

        print(f"🎉 All scripts have been processed and saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    process_scripts_parallel()
