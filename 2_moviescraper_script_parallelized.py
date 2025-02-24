import requests
import os
from bs4 import BeautifulSoup
import csv
from joblib import Parallel, delayed
from tqdm import tqdm
from tqdm_joblib import tqdm_joblib  # Fixes tqdm with joblib

SCRIPT_FOLDER = "movie_scripts"
NUM_WORKERS = 32

# Ensure the folder exists
os.makedirs(SCRIPT_FOLDER, exist_ok=True)

def scrape_script(title, script_url):
    """Scrapes an individual script and saves it as a text file."""
    try:
        response = requests.get(script_url, timeout=10)
        if response.status_code != 200:
            return f"Failed: {title}"

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract script content
        script_content = soup.find_all('pre')
        if script_content:
            script_text = str(script_content[0])

            # Define filename (Replace invalid characters in title)
            safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
            filename = os.path.join(SCRIPT_FOLDER, f"{safe_title}.txt")

            # Save script to file
            with open(filename, "w", encoding="utf-8") as file:
                file.write(script_text)

            return f"Saved: {title}"
        else:
            return f"Not Found: {title}"

    except requests.exceptions.RequestException as e:
        return f"Error: {title}"

def process_csv(filename="index.csv"):
    """Reads movie titles and script links from CSV and scrapes scripts in parallel."""
    with open(filename, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row

        movies = [(title, script_url) for title, script_url in reader]

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
