from google import genai
from dotenv import load_dotenv
import os
import pymongo
from fuzzywuzzy import process
from flask import Flask, request, jsonify
import requests


load_dotenv()
print("env loaded")

client = genai.Client(api_key=os.environ['API_KEY'])


#set mongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["movies_script_db"]
collection = db["character_dailouges"]

app = Flask(__name__)

@app.route("/chat", methods=["POST"])
def chat():
    
    data = request.get_json()
    character = data.get("character")
    user_message = data.get("user_message")

    if not character or not user_message:
        return jsonify({"error":"Character and user message is required"}),400
    
    print(f"{character}:{user_message}")

    dialouges = list(collection.find({"character":character},{"_id": 0, "dialogue": 1}))

    if dialouges:
        dialouges_texts = [d["dialouges"] for d in dialouges]
        best_match,score = process.extractOne(user_message,dialouges_texts)

        if score > 85:
            print(f"Found the match in MongoDB (Score:{score}):{best_match}")
            return jsonify({"character":character,"response":best_match,"ai_generated":False})
    print("No Match found in database. Using Gemini AI...")

    gemini_api_response = client.models.generate_content(
    model="gemini-2.0-flash", contents=f'''Hey Gemini, can u exactly respond like this {character} to this {user_message},
    STRICTLY IMITATE LIKE {character} BE AS PRECISE AS POSSIBLE, DO NOT SEND ANY IRRELEVANT TEXT AS I AM USING YOUR EXACT RESPONSE FOR AN AI CHARACTER VOICEBOT'''
        )

    ai_response = gemini_api_response.text
    return jsonify({"character":character,"response":ai_response,"ai_generated":True})
    



    # response = {
    #     "character": character,
    #     "user_message": user_message,
    #     "response": gemini_api_response.text
    # }

    # return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)