import requests
import csv
from bs4 import BeautifulSoup

BASE_URL = "https://imsdb.com/alphabetical/"
SCRIPT_URL = "https://imsdb.com/scripts/"

def get_movie_links(start_letter, end_letter):
    """Scrapes movie titles and script links from A to B and returns a list"""
    movie_data = []

    for letter in range(ord(start_letter), ord(end_letter) + 1):
        letter_url = f"{BASE_URL}{chr(letter)}"
        print(f"Scraping: {letter_url}")

        response = requests.get(letter_url)
        if response.status_code != 200:
            print(f"Failed to fetch {letter_url}")
            continue

        page = BeautifulSoup(response.text, "html.parser")
        tr = page.find_all('tr')
        tr = tr[3]
        tr = tr.find_all('td')
        tr = tr[73]
        tr = tr.find_all('a')

        for a in tr:
            title = a.text.strip()
            text = a['href'].split('/')[2]
            text = text.split(' ')[:-1]  # Remove the last word ('Script')

            text = '-'.join(text) + '.html'
            script_url = f"{SCRIPT_URL}{text}"

            movie_data.append([title, script_url])  # Append to list

    return movie_data

def save_to_csv(data, filename="index.csv"):
    """Saves the scraped movie data to CSV"""
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Script Link"])
        writer.writerows(data)
    print(f"Scraped {len(data)} movies and saved to {filename}")

if __name__ == "__main__":
    movies = get_movie_links("A", "Z")  # Scrape from A to B
    save_to_csv(movies)  # Save to CSV
