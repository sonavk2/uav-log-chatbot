# parser.py
from typing import Dict, List
from pymavlink import mavutil

def parse_log(file_path: str) -> Dict:
    mav = mavutil.mavlink_connection(file_path)

    data: Dict = {
        "raw_messages": [],
        "flight_time_sec": 0.0,
        "gps_events": []  
        "gps_events": []   
    }

    start_time = last_time = None

    gps_bad_times: List[float] = []

    while True:
        msg = mav.recv_match(blocking=False)
        if msg is None:
            break

        # Extract dict + timestamp
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

        cd = clean_fields(d)

        # Track GPS loss candidates
        if mtype in ("GPS", "GPS2", "GPS_RAW_INT", "GPS2_RAW"):
            nsats = cd.get("NSats") or cd.get("satellites_visible")
            fix   = cd.get("Status") or cd.get("FixType") or cd.get("fix_type")
            try:
                fix = int(fix) if fix is not None else None
            except Exception:
                fix = None

            if (nsats is not None and float(nsats) < 4) or (fix is not None and fix < 2):
                gps_bad_times.append(float(t))

        data["raw_messages"].append({
            "type": mtype,
            "time": float(t),
            "fields": cd
        })

    duration = round(last_time - start_time, 2) if (start_time is not None and last_time is not None) else 0.0
    data["flight_time_sec"] = duration

    anomalies: List[Dict] = []
    if gps_bad_times:
        gps_bad_times.sort()
        GAP = 3.0  
    # Duration
    duration = round(last_time - start_time, 2) if (start_time is not None and last_time is not None) else 0.0
    data["flight_time_sec"] = duration

    # Segment GPS bad windows into intervals
    anomalies: List[Dict] = []
    if gps_bad_times:
        gps_bad_times.sort()
        GAP = 3.0  # seconds — split if gaps are larger than this
        seg_start = gps_bad_times[0]
        prev = gps_bad_times[0]
        for t in gps_bad_times[1:]:
            if (t - prev) > GAP:
                anomalies.append({ "t": round(seg_start, 2), "type": "gps_dropout" })
                anomalies.append({ "t": round(prev, 2),      "type": "gps_recovered" })
                seg_start = t
            prev = t
        anomalies.append({ "t": round(seg_start, 2), "type": "gps_dropout" })
        anomalies.append({ "t": round(prev, 2),      "type": "gps_recovered" })

        # close final segment
        anomalies.append({ "t": round(seg_start, 2), "type": "gps_dropout" })
        anomalies.append({ "t": round(prev, 2),      "type": "gps_recovered" })

    kpis = {
        "flight_time_s": round(duration),
        "messages": len(data["raw_messages"])
    }

    data["meta"] = { "duration": duration }
    data["kpis"] = kpis
    data["anomalies"] = anomalies

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
