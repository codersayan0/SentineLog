import joblib
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from log_ingestor import parse_log_file, engineer_features, get_feature_columns

MODEL_PATH = "../models/isolation_forest.pkl"

def train_model(log_filepath: str):
    df = parse_log_file(log_filepath)
    df = engineer_features(df)
    features = df[get_feature_columns()].fillna(0)

    model = IsolationForest(
        n_estimators=100,
        contamination=0.08,
        random_state=42
    )
    model.fit(features)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model trained on {len(df)} log entries and saved.")
    return model

def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model not found. Run train_model() first.")
    return joblib.load(MODEL_PATH)

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    model = load_model()
    df = engineer_features(df)
    features = df[get_feature_columns()].fillna(0)

    # -1 = anomaly, 1 = normal
    df["prediction"] = model.predict(features)
    # Raw anomaly score — more negative = more anomalous
    df["anomaly_score"] = model.decision_function(features)
    # Normalize score to 0-100 for display
    raw = df["anomaly_score"].values
    df["anomaly_score_normalized"] = np.interp(raw, (raw.min(), raw.max()), (100, 0))

    anomalies = df[df["prediction"] == -1].copy()
    anomalies = anomalies.sort_values("anomaly_score_normalized", ascending=False)
    return anomalies

if __name__ == "__main__":
    train_model("../logs/sample_access.log")