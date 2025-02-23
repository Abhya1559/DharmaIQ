import requests
import os
import csv
from bs4 import BeautifulSoup
from joblib import Parallel, delayed
from tqdm import tqdm
from tqdm_joblib import tqdm_joblib  
from pymongo import MongoClient

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"  
DB_NAME = "MovieScriptsDB"
COLLECTION_NAME = "scripts"

# Create MongoDB client and get collection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

NUM_WORKERS = 32  # Parallel jobs

def scrape_script(title, script_url):
    """Scrapes an individual script and saves it to MongoDB."""
    try:
        response = requests.get(script_url, timeout=10)
        if response.status_code != 200:
            return f"Failed: {title}"

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract script content
        script_content = soup.find_all('pre')
        if script_content:
            script_text = script_content[0].get_text()

            # Store script in MongoDB
            collection.insert_one({
                "title": title,
                "script_url": script_url,
                "script_text": script_text
            })

            return f"Saved to MongoDB: {title}"
        else:
            return f"Not Found: {title}"

    except requests.exceptions.RequestException:
        return f"Error: {title}"

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

    # Use tqdm_joblib for proper progress tracking
    with tqdm_joblib(tqdm(desc="Scraping Scripts", total=len(movies), ncols=100)):
        results = Parallel(n_jobs=NUM_WORKERS, backend="threading")(
            delayed(scrape_script)(title, script_url) for title, script_url in movies
        )

    # Print summary
    for res in results:
        print(res)

if __name__ == "__main__":
    process_csv("index.csv")  # Read from index.csv and scrape scripts
