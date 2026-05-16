from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LogEntry(BaseModel):
    timestamp: str
    ip: str
    method: str
    endpoint: str
    status_code: int
    response_time: float
    payload_size: int
    user_agent: str

class Alert(BaseModel):
    id: Optional[int] = None
    timestamp: str
    ip: str
    anomaly_score: float
    threat_type: str
    severity: str
    explanation: str
    remediation: str
    raw_log: str