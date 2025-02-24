import streamlit as st
import requests

# Backend API URL
API_URL = "http://localhost:5000/chat"  # Change this to your deployed API

st.title("🎬 AI Movie Character Chatbot")

# Sidebar for character selection
st.sidebar.header("Select a Movie Character")
character = st.sidebar.text_input("Character Name", "Joker")

# Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
user_input = st.chat_input("Type your message...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Send request to backend
    response = requests.post(API_URL, json={"character": character, "user_message": user_input})
    if response.status_code == 200:
        bot_reply = response.json().get("response", "Error: No response from AI")
    else:
        bot_reply = "Error: Unable to connect to backend"
    
    st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.write(bot_reply)

# Upload movie script
st.sidebar.header("Upload Movie Script")
uploaded_file = st.sidebar.file_uploader("Upload a script (txt, pdf)", type=["txt", "pdf"])
if uploaded_file:
    st.sidebar.success("File uploaded successfully! (Processing not implemented)")
