from openai import OpenAI
from parser import flatten_telemetry
from vector_store import search_chunks
from sentence_transformers import SentenceTransformer
import os


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

model = SentenceTransformer('all-MiniLM-L6-v2')

def _format_anomalies(anoms):
    """anoms: list like [{'t': 73.8, 'type': 'gps_dropout'}, ...]"""
    if not anoms:
        return "None detected."
    lines = []

    stack = None
    for a in sorted(anoms, key=lambda x: float(x.get("t", 0))):
        t = float(a.get("t", 0))
        typ = str(a.get("type", "anomaly"))
        if typ.endswith("dropout") and stack is None:
            stack = t
        elif typ.startswith("gps_recov") and stack is not None:
            lines.append(f"GPS loss from {stack:.2f}s to {t:.2f}s.")
            stack = None
        else:
            lines.append(f"{typ} @ {t:.2f}s")
    if stack is not None:
        lines.append(f"GPS loss started at {stack:.2f}s (no end timestamp).")
    return "\n".join(lines)

def ask_llm(question, session_id, telemetry_data):
    chunks = flatten_telemetry(telemetry_data)
    flat_preview = "\n".join(chunks[:30])

    # 2) RAG context
    rag_hits = search_chunks(session_id, question, model)
    rag_context = "\n".join(rag_hits)

    # 3) Anomalies from parser output
    anomalies_list = telemetry_data.get("anomalies", [])
    anomaly_context = _format_anomalies(anomalies_list)

    # 4) KPIs / duration
    flight_time = telemetry_data.get("flight_time_sec") \
        or telemetry_data.get("meta", {}).get("duration") \
        or "N/A"

    user_prompt = f"""
Telemetry:
Computed flight time: {flight_time} seconds
{flat_preview}

Known Anomalies:
{anomaly_context}

Relevant Retrieved Info:
{rag_context}

User Question:
{question}
"""

    system_prompt = (
        "You are a smart, proactive UAV flight assistant. "
        "Use telemetry, anomalies, and retrieved context. "
        "Cite timestamps when possible and explain reasoning briefly. "
        "If something is missing, say what additional data would help."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",  
        model="gpt-4o-mini", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt.strip()},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content
