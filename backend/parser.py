from typing import Dict, List
from pymavlink import mavutil

def parse_log(file_path: str) -> Dict:
    mav = mavutil.mavlink_connection(file_path)

    data: Dict = {
        "raw_messages": [],
        "flight_time_sec": 0.0,
        "gps_events": []
    }

    start_time = last_time = None

    while True:
        msg = mav.recv_match(blocking=False)
        if msg is None:
            break
        t = None
        if hasattr(msg, "to_dict"):
            try:
                d = msg.to_dict()
                t_us = d.get("TimeUS")
                if t_us:
                    t = float(t_us) / 1e6
            except Exception:
                d = {}
        else:
            d = {}

        if t is None:
            t = getattr(msg, "_timestamp", None)
        
        if t is None:
            continue

        if start_time is None:
            start_time = t

        last_time = t

        mtype = msg.get_type()
        
        def clean_fields(fields):
            cleaned = {}
            for k, v in fields.items():
                if isinstance(v, (int, float, str, bool, type(None))):
                    cleaned[k] = v
                else:
                    try:
                        cleaned[k] = str(v)
                    except Exception:
                        cleaned[k] = None
            return cleaned

        data["raw_messages"].append({
            "type": mtype,
            "time": t,
            "fields": clean_fields(d)
        })


    data["flight_time_sec"] = round(last_time - start_time, 2) if (start_time is not None and last_time is not None) else 0.0
    return data

def flatten_telemetry(data: Dict, prefix="") -> List[str]:
    out = []
    for k, v in data.items():
        label = f"{prefix}{k}"
        if isinstance(v, dict):
            out.extend(flatten_telemetry(v, prefix=label + "."))
        elif isinstance(v, list):
            preview = v[:3] if len(v) > 3 else v
            out.append(f"{label}: {preview} (truncated)" if len(v) > 3 else f"{label}: {v}")
        else:
            out.append(f"{label}: {v}")
    return out


def detect_anomalies(parsed_data):
    anomalies = {}
    gps_loss_events = []

    for msg in parsed_data["raw_messages"]:
        if msg["type"] == "GPS":
            fields = msg["fields"]
            nsats = fields.get("NSats")
            fix = fields.get("Status") or fields.get("FixType")
            if (nsats is not None and nsats < 4) or (fix is not None and int(fix) < 2):
                gps_loss_events.append(msg["time"])

    if gps_loss_events:
        start = round(gps_loss_events[0], 2)
        end = round(gps_loss_events[-1], 2)
        anomalies["gps"] = f"Possible GPS loss between {start}s and {end}s (low satellite count or no fix)."

    return anomalies
