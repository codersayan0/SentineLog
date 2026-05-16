import requests
import os
from dotenv import load_dotenv

load_dotenv()
ABUSEIPDB_KEY = os.getenv("ABUSEIPDB_KEY")

def check_ip(ip: str) -> dict:
    if not ABUSEIPDB_KEY:
        return {"abuse_confidence": 0, "total_reports": 0, "country": "Unknown"}

    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {"Key": ABUSEIPDB_KEY, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": 90}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json().get("data", {})
        return {
            "abuse_confidence": data.get("abuseConfidenceScore", 0),
            "total_reports": data.get("totalReports", 0),
            "country": data.get("countryCode", "Unknown"),
            "isp": data.get("isp", "Unknown"),
            "is_tor": data.get("isTor", False),
        }
    except Exception as e:
        print(f"AbuseIPDB lookup failed: {e}")
        return {"abuse_confidence": 0, "total_reports": 0, "country": "Unknown"}