import { useMemo, useRef, useState } from "react";

const API_BASE = "http://localhost:8000"; // change if your FastAPI runs elsewhere

export default function App() {
  const [file, setFile] = useState(null);
  const [sessionId, setSessionId] = useState("");
  const [telemetry, setTelemetry] = useState(null);
  const [uploading, setUploading] = useState(false);

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [asking, setAsking] = useState(false);

  const [playhead, setPlayhead] = useState(0);
  const barRef = useRef(null);

  const anomalies = useMemo(() => {
    if (!telemetry) return [];
    return telemetry.anomalies || telemetry.events || telemetry.detections || [];
  }, [telemetry]);

  const duration = useMemo(() => {
    if (!telemetry) return 0;
    const d = telemetry.meta?.duration || telemetry.duration;
    if (d) return Math.ceil(Number(d));
    const maxT = anomalies.reduce((m, a) => Math.max(m, Number(a.t ?? a.ts ?? 0)), 0);
    return Math.ceil(maxT || 0);
  }, [telemetry, anomalies]);

  const kpis = useMemo(() => telemetry && (telemetry.kpis || telemetry.summary) || null, [telemetry]);

  const handleFileChange = (e) => setFile(e.target.files?.[0] || null);

  const handleUpload = async () => {
    if (!file) return alert("Choose a .bin log first");
    setUploading(true);
    setAnswer("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API_BASE}/upload-log`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      setSessionId(json.session_id);
      setTelemetry(json.data);
    } catch (err) {
      console.error(err);
      alert("Upload failed: " + (err?.message || err));
    } finally {
      setUploading(false);
    }
  };

  const onTimelineClick = (e) => {
    if (!duration || !barRef.current) return;
    const rect = barRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const frac = Math.min(Math.max(x / rect.width, 0), 1);
    setPlayhead(Math.round(frac * duration));
  };

  const jumpTo = (t) => setPlayhead(Math.round(Number(t)));

  const handleAsk = async () => {
    if (!question.trim()) return;
    if (!sessionId) return alert("Upload a log first");
    setAsking(true);
    setAnswer("");
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, question }),
      });
      if (!res.ok) throw new Error(await res.text());
      const json = await res.json();
      setAnswer(json.answer || "(no answer)");
    } catch (err) {
      console.error(err);
      setAnswer("Error: " + (err?.message || err));
    } finally {
      setAsking(false);
    }
  };

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>UAV Log Chatbot</h1>

      <section style={styles.card}>
        <h2 style={styles.h2}>1) Upload your flight log (.bin)</h2>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <input type="file" accept=".bin" onChange={handleFileChange} />
          <button onClick={handleUpload} disabled={!file || uploading} style={styles.btn}>
            {uploading ? "Uploading…" : "Upload & Parse"}
          </button>
          {sessionId && <span style={styles.badge}>Session: {sessionId}</span>}
        </div>

        {kpis && (
          <div style={{ marginTop: 12, display: "flex", gap: 10, flexWrap: "wrap" }}>
            {Object.entries(kpis).map(([k, v]) => (
              <Kpi key={k} label={k} value={String(v)} />
            ))}
          </div>
        )}
      </section>

      <section style={styles.card}>
        <h2 style={styles.h2}>2) Timeline & Anomalies</h2>
        <div ref={barRef} style={styles.timeline} onClick={onTimelineClick} title="Click to move playhead">
          <div style={{ ...styles.playhead, left: duration ? `${(playhead / duration) * 100}%` : 0 }} />
          {anomalies.map((a, i) => {
            const t = Number(a.t ?? a.ts ?? 0);
            const left = duration ? Math.min(100, Math.max(0, (t / duration) * 100)) : 0;
            return (
              <div
                key={i}
                title={`${a.type || a.reason || "anomaly"} @ ${t.toFixed(1)}s`}
                style={{ ...styles.marker, left: `${left}%` }}
                onClick={(e) => { e.stopPropagation(); jumpTo(t); }}
              />
            );
          })}
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
          {anomalies.length === 0 && <span style={{ opacity: 0.7 }}>No anomalies detected</span>}
          {anomalies.slice(0, 14).map((a, i) => (
            <span key={i} style={styles.chip} onClick={() => jumpTo(Number(a.t ?? a.ts ?? 0))}>
              {(a.type || a.reason || "anomaly").toString()} @ {Number(a.t ?? a.ts ?? 0).toFixed(1)}s
            </span>
          ))}
        </div>
      </section>

      <section style={styles.card}>
        <h2 style={styles.h2}>3) Ask about your flight</h2>
        <div style={{ display: "flex", gap: 10 }}>
          <input
            style={styles.input}
            placeholder="e.g., Why did RTL trigger? Any GPS dropouts around 120s?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            disabled={!sessionId}
          />
          <button style={styles.btn} onClick={handleAsk} disabled={!sessionId || asking}>
            {asking ? "Asking…" : "Ask"}
          </button>
        </div>
        {answer && (
          <div style={styles.answerBox}>
            <strong>Answer</strong>
            <div>{answer}</div>
          </div>
        )}
      </section>

      <footer style={{ textAlign: "center", opacity: 0.6, marginTop: 20 }}>
        <small>UI connected to {API_BASE}</small>
      </footer>
    </div>
  );
}

function Kpi({ label, value }) {
  return (
    <div style={styles.kpi}>
      <div style={{ fontSize: 12, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 600 }}>{value}</div>
    </div>
  );
}

const styles = {
  page: { maxWidth: 920, margin: "40px auto", padding: "0 16px", color: "#E5E7EB" },
  title: { fontSize: 56, margin: "0 0 20px 0", color: "#F3F4F6" },
  card: { background: "#111827", border: "1px solid #374151", borderRadius: 12, padding: 16, marginBottom: 16 },
  h2: { margin: 0, marginBottom: 10, fontSize: 18, color: "#F9FAFB" },
  btn: { background: "#111111", color: "white", padding: "8px 12px", borderRadius: 8, border: "1px solid #333", cursor: "pointer" },
  badge: { background: "#1F2937", border: "1px solid #374151", padding: "4px 8px", borderRadius: 999, fontSize: 12 },
  timeline: { position: "relative", height: 24, background: "linear-gradient(90deg,#1F2937,#0F172A)", borderRadius: 999, border: "1px solid #374151" },
  playhead: { position: "absolute", top: -6, width: 2, height: 36, background: "#F9FAFB", transform: "translateX(-1px)" },
  marker: { position: "absolute", top: 2, width: 8, height: 20, background: "#EF4444", borderRadius: 3, transform: "translateX(-4px)", cursor: "pointer" },
  chip: { background: "#7F1D1D", color: "#FECACA", border: "1px solid #B91C1C", borderRadius: 999, padding: "4px 10px", fontSize: 12, cursor: "pointer" },
  input: { flex: 1, padding: 10, borderRadius: 8, border: "1px solid #374151", background: "#0B1220", color: "#E5E7EB" },
  answerBox: { marginTop: 12, background: "#0B1220", border: "1px solid #374151", borderRadius: 8, padding: 12 },
  kpi: { background: "#0B1220", border: "1px solid #374151", borderRadius: 8, padding: "8px 10px", minWidth: 140 },
};
