from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from parser import parse_log
from llm_utils import ask_llm
import shutil, os, math

UPLOAD_DIR = "backend/uploaded_logs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
telemetry_cache = {}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    session_id: str
    question: str

def sanitize_json(obj):
        if isinstance(obj, dict):
            return {k: sanitize_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_json(i) for i in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        return obj

@app.post("/upload-log")
async def upload_log(file: UploadFile = File(...)):
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    parsed = parse_log(file_location)
    telemetry_cache[file.filename] = parsed

    return {
        "message": "File parsed successfully",
        "data": sanitize_json(parsed),
        "session_id": file.filename
    }


@app.post("/ask")
async def ask_question(req: AskRequest):
    session_id, question = req.session_id, req.question
    telemetry_data = telemetry_cache.get(session_id)
    if telemetry_data is None:
        telemetry_data = parse_log(f"{UPLOAD_DIR}/{session_id}")
    return {"answer": ask_llm(question, session_id, telemetry_data)}
