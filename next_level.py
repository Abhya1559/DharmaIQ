import requests
import os
import csv
import re
import json
import time
import faiss
import numpy as np
from bs4 import BeautifulSoup
from pymongo import MongoClient
from joblib import Parallel, delayed
from tqdm import tqdm
from tqdm_joblib import tqdm_joblib  
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Load environment variables
load_dotenv()
print("\u2705 Environment Loaded")

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Movie"
COLLECTION_NAME = "scripts"
CLEANED_COLLECTION = "cleaned_scripts"

# Parallel processing
NUM_WORKERS = 16  # Adjust based on CPU cores

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
cleaned_collection = db[CLEANED_COLLECTION]

VECTOR_DIMENSION = 768 
faiss_index = faiss.IndexFlatL2(VECTOR_DIMENSION)
dialogue_mapping = []  

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text):
    """Generates an embedding for a given text using SentenceTransformer."""
    return embedding_model.encode(text, convert_to_numpy=True)

def index_movie_dialogues():
    """Extracts dialogues from MongoDB, generates embeddings, and stores them in FAISS."""
    global dialogue_mapping
    
    scripts = cleaned_collection.find({}, {"_id": 0, "title": 1, "characters": 1})
    dialogue_data = []
    
    for script in tqdm(scripts, desc="Indexing Dialogues", ncols=100):
        title = script.get("title", "Unknown Title")
        characters = script.get("characters", {})
        for character, lines in characters.items():
            for line in lines:
                cleaned_line = line.strip()
                if cleaned_line:
                    embedding = get_embedding(cleaned_line)
                    dialogue_data.append((embedding, cleaned_line, title, character))
    
    if dialogue_data:
        embeddings = np.array([d[0] for d in dialogue_data], dtype=np.float32)
        embeddings = embeddings.reshape(-1, VECTOR_DIMENSION)  
        faiss_index.add(embeddings)
        dialogue_mapping.extend([(d[1], d[2], d[3]) for d in dialogue_data]) 
        print("\u2705 FAISS Index Built!")
    else:
        print("\u26A0 No dialogues found for indexing!")

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    """Handles chat requests by retrieving similar movie dialogues or generating responses."""
    data = request.json
    user_input = data.get("message", "").strip()
    
    if not user_input:
        return jsonify({"error": "Message is required!"}), 400
    
    input_embedding = get_embedding(user_input).reshape(1, -1)
    
    if faiss_index.ntotal == 0:
        return jsonify({"error": "No dialogues indexed yet. Please add movie dialogues."}), 500
    
    _, indices = faiss_index.search(input_embedding, 1)
    closest_index = indices[0][0]
    
    if closest_index >= 0 and closest_index < len(dialogue_mapping):
        closest_dialogue, movie, character = dialogue_mapping[closest_index]
        return jsonify({"response": closest_dialogue, "movie": movie, "character": character})
    
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"{user_input} (If this is from a movie, respond in character.)"
    
    try:
        response = model.generate_content(prompt)
        ai_response = response.text if response and hasattr(response, 'text') else "I couldn't find a relevant movie dialogue."
    except Exception as e:
        ai_response = f"AI Error: {str(e)}"

    return jsonify({"response": ai_response})

if __name__ == "__main__":
    index_movie_dialogues() 
    app.run(debug=True, use_reloader=False)
