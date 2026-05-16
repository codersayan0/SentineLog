import re
import pandas as pd
from datetime import datetime

LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) - - \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<endpoint>\S+) HTTP/\S+" '
    r'(?P<status_code>\d+) (?P<payload_size>\d+) '
    r'"(?P<user_agent>[^"]+)" (?P<response_time>[\d.]+)'
)

def parse_log_line(line: str) -> dict | None:
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None
    data = match.groupdict()
    data["status_code"] = int(data["status_code"])
    data["payload_size"] = int(data["payload_size"])
    data["response_time"] = float(data["response_time"])
    return data

def parse_log_file(filepath: str) -> pd.DataFrame:
    entries = []
    with open(filepath, "r") as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed:
                entries.append(parsed)
    df = pd.DataFrame(entries)
    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    # Requests per IP (attack indicator — high count from one IP)
    ip_counts = df.groupby("ip").size().reset_index(name="requests_per_ip")
    df = df.merge(ip_counts, on="ip", how="left")

    # Error rate per IP (brute force = many 401/403)
    df["is_error"] = df["status_code"].apply(lambda x: 1 if x >= 400 else 0)
    error_rate = df.groupby("ip")["is_error"].mean().reset_index(name="error_rate")
    df = df.merge(error_rate, on="ip", how="left")

    # Suspicious endpoint flag
    suspicious = ["admin", "wp-login", ".env", "phpmyadmin", "config", "sql", "OR"]
    df["suspicious_endpoint"] = df["endpoint"].apply(
        lambda x: 1 if any(s.lower() in x.lower() for s in suspicious) else 0
    )

    # Suspicious user agent flag
    bad_agents = ["sqlmap", "nikto", "curl", "python-requests"]
    df["suspicious_agent"] = df["user_agent"].apply(
        lambda x: 1 if any(a.lower() in x.lower() for a in bad_agents) else 0
    )

    return df

def get_feature_columns():
    return [
        "requests_per_ip",
        "error_rate",
        "response_time",
        "payload_size",
        "suspicious_endpoint",
        "suspicious_agent",
    ]