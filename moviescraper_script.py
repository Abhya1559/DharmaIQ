import requests
import os
from bs4 import BeautifulSoup
import csv

SCRIPT_FOLDER = "movie_scripts"

# Ensure the folder exists
os.makedirs(SCRIPT_FOLDER, exist_ok=True)

def scrape_script(title, script_url):
    """Scrapes an individual script and saves it as a text file"""
    print(f"Fetching script: {title}")

    response = requests.get(script_url)
    if response.status_code != 200:
        print(f"Failed to fetch {script_url}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract script content using the given XPath structure
    script_content= soup.find_all('pre')
    script_content=soup.find_all('pre')[0]
  

    if script_content:
        script_text = script_content

        # Define filename (Replace invalid characters in title)
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
        filename = os.path.join(SCRIPT_FOLDER, f"{safe_title}.txt")

        # Save script to file
        with open(filename, "w", encoding="utf-8") as file:
            file.write(str(script_text))

        print(f"Saved: {filename}")
    else:
        print(f"Script content not found for {title}")

def process_csv(filename="index.csv"):
    """Reads movie titles and script links from CSV and scrapes scripts"""
    with open(filename, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Skip header row

        for row in reader:
            title, script_url = row
            scrape_script(title, script_url)
            

if __name__ == "__main__":
    process_csv("index.csv")  # Read from index.csv and scrape scripts
