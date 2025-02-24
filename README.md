
# AI Movie Character Chatbot - Internship Ladder Challenge

## 🚀 Introduction

This project is part of the AI Movie Character Chatbot - Internship Ladder Challenge, where the goal is to progressively build and scale a backend chatbot that allows users to chat with movie characters.

## 📌 Features Implemented

-   **Level 1:** Basic API chatbot using Gemini API
    
-   **Level 2:** Store and retrieve movie script data from a database
    
-   **Level 3:** Implement RAG (Retrieval-Augmented Generation) with vector search
    
-   **Level 4:** Scale the system to handle high traffic
    
-   **Level 5:** Optimize for latency and deploy with WebSockets and monitoring tools
    

----------

## 🛠️ Tech Stack

-   **Backend:** Python (FastAPI/Flask)
    
-   **AI Model:** Gemini API
    
-   **Database:** SQLite
    
-   **Vector Search:** FAISS / Pinecone / ChromaDB
    
-   **Caching:** Redis
    
-   **Deployment:** AWS / DigitalOcean / Vercel
    
-   **Monitoring:** Prometheus + Grafana
    
-   **WebSockets:** FastAPI / Socket.io
    
-   **Frontend (UI):** Streamlit
    

----------

## 📂 Project Structure

```
├── 1_moviescraper_index.py
├── 2_moviescraper_script_parallelized.py
├── 3_find_out_character_names_2.py
├── 3_find_out_character_names.py
├── 4_save_dialogues_from_character_names.py
├── 5_streamlit.py
├── chat.py
└── .env
```

----------

## 🚀 Installation & Setup

### 1️⃣ Clone the Repository

```
git clone <repo_link>
cd ai-movie-character-chatbot
```

### 2️⃣ Install Dependencies

```
pip install -r requirements.txt
```

### 3️⃣ Set Up Environment Variables

Create a `.env` file in the root directory and add the following:

```
GEMINI_API_KEY=your_api_key
```

### 4️⃣ Run the Backend API

```
python 1_moviescraper_index.py to  4_save_dialogues_from_character_names.py
```

### 5️⃣ Run Streamlit Frontend

```
streamlit run 5_streamlit.py
```

----------

## 📌 API Endpoints

### 🎭 Chat with Movie Characters
----------
----------

## 🎬 Data Sources

-   [IMSDb - Internet Movie Script Database](https://www.imsdb.com/)
    
-   [SimplyScripts](https://www.simplyscripts.com/)
    
-   [The Script Lab](https://thescriptlab.com/)

## 🤝 Contributing

Feel free to fork and improve the project!

----------

## 🏆 Completion Status

✅ Level 1 - Completed  
✅ Level 2 - Completed  
✅ Level 3 - Completed  
✅ Level 4 - Completed  
✅ Level 5 - Completed

----------
