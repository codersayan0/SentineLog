import os
import pandas as pd
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from datetime import datetime

from database import get_db, AlertDB
from log_ingestor import parse_log_file, engineer_features, get_feature_columns
from anomaly_detector import detect_anomalies, train_model
from llm_explainer import explain_threat
from abuseipdb import check_ip
from models import Alert

load_dotenv()

app = FastAPI(title="SentinelLog API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_FILE = os.getenv("LOG_FILE", "../logs/sample_access.log")

@app.get("/")
def root():
    return {"status": "SentinelLog is running", "version": "1.0.0"}

@app.get("/logs")
def get_logs(limit: int = 100):
    df = parse_log_file(LOG_FILE)
    return {"total": len(df), "logs": df.tail(limit).to_dict(orient="records")}

@app.post("/analyze")
def analyze_logs(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(run_analysis, db)
    return {"message": "Analysis started in background"}

def run_analysis(db: Session):
    df = parse_log_file(LOG_FILE)
    anomalies = detect_anomalies(df)

    for _, row in anomalies.iterrows():
        ip_report = check_ip(row["ip"])
        features = {col: row[col] for col in get_feature_columns()}
        raw_log = (
            f'{row["ip"]} [{row["timestamp"]}] '
            f'"{row["method"]} {row["endpoint"]}" '
            f'{row["status_code"]} {row["response_time"]}'
        )
        result = explain_threat(
            log_entry=raw_log,
            anomaly_score=row["anomaly_score_normalized"],
            ip_report=ip_report,
            features=features,
        )

        alert = AlertDB(
            timestamp=row["timestamp"],
            ip=row["ip"],
            anomaly_score=row["anomaly_score_normalized"],
            threat_type=result["threat_type"],
            severity=result["severity"],
            explanation=result["explanation"],
            remediation=result["remediation"],
            raw_log=raw_log,
        )
        db.add(alert)

    db.commit()
    print(f"Analysis done — {len(anomalies)} anomalies processed.")

@app.get("/alerts")
def get_alerts(limit: int = 50, severity: str = None, db: Session = Depends(get_db)):
    query = db.query(AlertDB).order_by(AlertDB.id.desc())
    if severity:
        query = query.filter(AlertDB.severity == severity)
    alerts = query.limit(limit).all()
    return {"total": len(alerts), "alerts": [
        {
            "id": a.id,
            "timestamp": a.timestamp,
            "ip": a.ip,
            "anomaly_score": round(a.anomaly_score, 1),
            "threat_type": a.threat_type,
            "severity": a.severity,
            "explanation": a.explanation,
            "remediation": a.remediation,
            "raw_log": a.raw_log,
        }
        for a in alerts
    ]}

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(AlertDB).count()
    critical = db.query(AlertDB).filter(AlertDB.severity == "critical").count()
    high = db.query(AlertDB).filter(AlertDB.severity == "high").count()
    medium = db.query(AlertDB).filter(AlertDB.severity == "medium").count()
    low = db.query(AlertDB).filter(AlertDB.severity == "low").count()
    unique_ips = db.query(AlertDB.ip).distinct().count()

    return {
        "total_alerts": total,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "unique_ips_flagged": unique_ips,
    }

@app.post("/train")
def train(log_file: str = LOG_FILE):
    train_model(log_file)
    return {"message": f"Model trained on {log_file}"}