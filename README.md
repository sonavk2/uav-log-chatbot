# UAV Log Chatbot

An agentic chatbot backend that analyzes UAV flight logs and answers questions using LLMs. This project extends the functionality of the [UAVLogViewer](https://github.com/ArduPilot/UAVLogViewer) by integrating a Python backend that parses `.bin` log files, detects anomalies, and allows users to chat with the system about their flight data.

## Features

- Upload a `.bin` MAVLink flight log
- Ask questions like:
  - "What was the maximum altitude?"
  - "Did the GPS signal drop mid-flight?"
  - "Are there any anomalies?"
- Detects GPS issues and flight anomalies automatically
- Maintains conversation context and asks clarifying questions
- Uses OpenAI's GPT-4 + FAISS + sentence-transformers for RAG

---
## Project Structure
uav-log-chatbot/
├── backend/
│ ├── main.py # FastAPI backend
│ ├── parser.py # MAVLink log parser
│ ├── llm_utils.py # LLM interaction logic
│ ├── vector_store.py # FAISS-based vector retrieval
│ ├── requirements.txt # Python dependencies
│ └── uploaded_logs/ # Temporarily stored flight logs
├── README.md
└── UAVLogViewer/ # (Optional) Original viewer frontend (unchanged)

## Setup Instructions

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

