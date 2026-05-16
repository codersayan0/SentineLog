import os
import json
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.2,
)

prompt_template = PromptTemplate(
    input_variables=["log_entry", "anomaly_score", "ip_report", "features"],
    template="""
You are a senior cybersecurity analyst working in a SOC.

A machine learning model flagged this log entry as suspicious:

Log entry: {log_entry}
Anomaly score (0-100, higher = more suspicious): {anomaly_score}
IP threat intelligence: {ip_report}
Extracted features: {features}

Respond ONLY with a valid JSON object — no text outside the JSON:

{{
  "threat_type": "one of: brute_force, sql_injection, ddos, port_scan, data_exfiltration, reconnaissance, unknown",
  "severity": "one of: low, medium, high, critical",
  "explanation": "2 sentence plain English explanation of what this threat is",
  "remediation": "1 specific action to take immediately"
}}
"""
)

chain = prompt_template | llm | StrOutputParser()

def explain_threat(log_entry: str, anomaly_score: float, ip_report: dict, features: dict) -> dict:
    try:
        response = chain.invoke({
            "log_entry"    : log_entry,
            "anomaly_score": round(anomaly_score, 2),
            "ip_report"    : json.dumps(ip_report),
            "features"     : json.dumps(features),
        })
        cleaned = response.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned)
    except Exception as e:
        print(f"LLM explainer error: {e}")
        return {
            "threat_type" : "unknown",
            "severity"    : "medium",
            "explanation" : "Anomaly detected but explanation unavailable.",
            "remediation" : "Review log entry manually.",
        }