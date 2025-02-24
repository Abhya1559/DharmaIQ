import os
import csv
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv
import re
import json

load_dotenv()

SCRIPT_FOLDER = "movie_scripts"
OUTPUT_CSV = "character_names.csv"

def extract_bold_names(script_text):
    """Extracts unique names from <b> tags in the script."""
    soup = BeautifulSoup(script_text, "html.parser")
    bold_tags = soup.find_all("b")
    
    # Extract text, strip spaces, remove empty strings
    names = list(set(tag.get_text(strip=True) for tag in bold_tags if tag.get_text(strip=True)))
    
    return names



def clean_and_parse_json(text):

    
    cleaned = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)

    return json.loads(cleaned)


def check_character_names(script_name,names):
    """Sends names to Gemini API to filter out character names."""
    client = genai.Client(api_key=os.environ["API_KEY_2"])
   
    
    prompt = f"""

    Hey Gemini! I am building a project that requires extracting character names from movie scripts.
    the script's filename is {script_name} and the character names are
    {names}
    Return strictly in JSON Format with the key being character and the value being the names of the character in list format.
    DO NOT RETURN ANYTHING ELSE OTHER THAN THE CHARACTER NAMES. STRICTLY FOLLOW ALL MY INSTRUCTIONS GIVEN.
    Please return only the names that belong to characters in the script. Exclude any non-character words.
    """
  

    
    try:
        response = client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )
        response=clean_and_parse_json(response.text)
        
    
         
        return response[list(response.keys())[0]]
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return []

def process_scripts():
    """Processes all scripts in the folder, extracts character names, and saves them to CSV."""
    data = []
    all_files=os.listdir(SCRIPT_FOLDER)
    all_files.sort()
    all_files=all_files[len(all_files)//2:]
    for filename in all_files:
        if filename.endswith(".txt"):
            filepath = os.path.join(SCRIPT_FOLDER, filename)
            print(f"Processing: {filename}")

            # Read script text
            with open(filepath, "r", encoding="utf-8") as file:
                script_text = file.read()

            # Extract names from <b> tags
            extracted_names = extract_bold_names(script_text)

            # Validate character names using Gemini API
            character_names = check_character_names(filename,extracted_names)

            # Append results
            data.append([filename, ", ".join(character_names)])
            

    # Save to CSV
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Script Name", "Character Names"])
        writer.writerows(data)

    print(f"Saved extracted character names to {OUTPUT_CSV}")

if __name__ == "__main__":
    process_scripts()
