# UAV Log Chatbot

An agentic UAV flight log analysis tool with a Python backend and a modern React frontend.
Upload .bin MAVLink flight logs, detect anomalies, and chat with an AI assistant about your UAV's performance.

## Features

- Upload & parse .bin MAVLink flight logs
- Ask natural language questions like:
  - "What was the maximum altitude?"
  - "Did the GPS signal drop mid-flight?"
  - "Show me the flight timeline"
  - "Are there any anomalies?"
- Automatic anomaly detection:
  - GPS signal dropouts & recoveries
  - Radio/GCS failsafe events
  - Other detected telemetry irregularities
- Flight timeline extraction
- Maintains conversation context
- Uses OpenAI's GPT-4 + FAISS + sentence-transformers for RAG

---
## Project Structure
```
uav-log-chatbot/
├── backend/
│   ├── main.py             # FastAPI backend
│   ├── parser.py           # MAVLink log parser & anomaly detection
│   ├── llm_utils.py        # LLM integration & prompt building
│   ├── vector_store.py     # FAISS-based vector search
│   ├── requirements.txt    # Python dependencies
│   └── uploaded_logs/      # Temporary storage for uploaded logs
├── frontend/
│   ├── src/                # React components & pages
│   ├── public/             # Static assets
│   ├── package.json        # Frontend dependencies
│   └── vite.config.js      # Vite config
└── README.md

```

## Setup Instructions

**Backend Setup (FastAPI)**
1. Clone this repo
git clone https://github.com/sonavk2/uav-log-chatbot.git
cd uav-log-chatbot/backend

2. Install dependencies
pip install -r requirements.txt

3. Set your OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"

4. Run the backend server
uvicorn main:app --reload

5. Send a POST request to the backend:

curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
        "session_id": "1980-01-08 09-44-08.bin",
        "question": "Did the UAV experience any unexpected altitude drops?"
      }'


**Frontend Setup (React + Vite)**
1. Open a new terminal
cd ../frontend

2. Install Node.js dependencies
npm install

3. Start the development server
npm run dev

