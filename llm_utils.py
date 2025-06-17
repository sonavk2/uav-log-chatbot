from openai import OpenAI
from parser import flatten_telemetry, detect_anomalies
from vector_store import search_chunks
from sentence_transformers import SentenceTransformer

client = OpenAI(api_key="OPENAI_API_KEY")

model = SentenceTransformer('all-MiniLM-L6-v2')

def ask_llm(question, session_id, telemetry_data):
    chunks = flatten_telemetry(telemetry_data)
    rag_context = "\n".join(search_chunks(session_id, question, model))
    anomalies = detect_anomalies(telemetry_data)
    anomaly_context = "\n".join([f"{k.upper()} anomaly: {v}" for k, v in anomalies.items()]) or "None detected."

    flight_time_line = f"Computed flight time: {telemetry_data.get('flight_time_sec', 'N/A')} seconds"

    user_prompt = f"""
Telemetry:
{flight_time_line}
{chr(10).join(chunks[:30])}

Known Anomalies:
{anomaly_context}

Relevant Retrieved Info:
{rag_context}

User Question:
{question}
"""

    system_prompt = (
    "You are a smart, proactive UAV flight assistant. Use all telemetry and context to help. "
    "If you can’t find a direct answer, consider alternative data sources. "
    "Ask follow-up questions if something is unclear or seems missing. Maintain the context of the conversation."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content