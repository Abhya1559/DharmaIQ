from flask import Flask, request
from flask_socketio import SocketIO, emit
import pymongo
import os
from google import genai
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
print("✅ Environment Loaded")

# Initialize MongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["movie_scripts_db"]
chat_collection = db["chat_history"]

# Initialize Flask and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Google Gemini AI Client
client = genai.Client(api_key=os.environ['API_KEY'])

@socketio.on("message")
def handle_message(data):
    """Handles real-time chat using WebSockets"""
    user_id = data.get("user_id")
    character = data.get("character")
    user_message = data.get("user_message")

    if not user_id or not character or not user_message:
        emit("response", {"error": "Missing required fields"})
        return

    start_time = time.time()

    # Check MongoDB for stored dialogues
    dialogue = chat_collection.find_one({"character": character, "user_message": user_message}, {"_id": 0, "response": 1})

    if dialogue:
        response = dialogue["response"]
        ai_generated = False
    else:
        # Use Gemini AI if no match found
        print("⚡ No match found in DB. Using Gemini AI...")
        gemini_api_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Hey Gemini, act exactly like {character}. Respond naturally to this input: {user_message}."
        )
        response = gemini_api_response.text
        ai_generated = True

        # Store the response in MongoDB for future use
        chat_collection.insert_one({
            "user_id": user_id,
            "character": character,
            "user_message": user_message,
            "response": response,
            "ai_generated": ai_generated
        })

    # Emit response
    emit("response", {"character": character, "response": response, "ai_generated": ai_generated})

    # Track response time
    end_time = time.time()
    print(f"Response Time: {round((end_time - start_time) * 1000, 2)}ms")

# Run Flask app
if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
