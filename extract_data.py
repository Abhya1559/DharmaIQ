import re
import pymongo

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["movie_scripts_db"]
collection = db["character_dialogues"]  # Fixed spelling

def extract_dialogues(script_text, movie_title):
    dialogues = []
    lines = script_text.split("\n")
    character = None

    for line in lines:
        line = line.strip()

        # Check if the line is a character name (all uppercase, short length)
        if re.match(r"^[A-Z][A-Z\s]+$", line) and len(line) < 30:
            character = line.strip()  # Set the current character
        
        # If the current line is not a character name, treat it as dialogue
        elif character and line:
            dialogues.append({
                "movie": movie_title,
                "character": character,
                "dialogue": line  # Store only the dialogue, not the entire script
            })
    
    return dialogues

# Sample script text
script_text = """JACK  
I can't believe we are doing this.  

ROSE  
Just trust me."""

movie_title = "Titanic"

# Extract dialogues
extracted_data = extract_dialogues(script_text, movie_title)

# Store in MongoDB
if extracted_data:
    collection.insert_many(extracted_data)
    print("Dialogues have been stored in MongoDB successfully.")
else:
    print("No dialogues found to store.")
