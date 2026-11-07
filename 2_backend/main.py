import os
import json
import traceback
import urllib.request

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------- Read .env without any extra package ----------
if os.path.exists(".env"):
    with open(".env", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

# ---------- App ----------
app = FastAPI(title="AI Healthcare Network")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Load model (works with both old and new model.pkl) ----------
saved = joblib.load("model.pkl")

if isinstance(saved, dict) and "model" in saved:
    model = saved["model"]
    columns = list(saved["columns"])
else:
    model = saved
    columns = [
        "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
        "thalach", "exang", "oldpeak", "slope", "ca", "thal",
    ]

print("Model loaded:", type(model).__name__)
print("Columns expected:", columns)


class PatientData(BaseModel):
    age: float
    sex: float
    cp: float
    trestbps: float
    chol: float
    fbs: float
    restecg: float
    thalach: float
    exang: float
    oldpeak: float
    slope: float
    ca: float
    thal: float


# ---------- Gemini explanation (never crashes the app) ----------
def explain_with_gemini(data: dict, risk_percent: float, level: str) -> str:
    fallback = (
        f"The model estimates a {level} risk ({risk_percent}%) based on the values entered. "
        "Please consult a doctor for a proper check-up."
    )
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return fallback

    prompt = (
        "You are a health assistant. Explain this heart risk result in simple words "
        "in 4 short sentences. Do not diagnose. Do not prescribe medicine. "
        "End by advising to consult a doctor.\n"
        f"Risk: {risk_percent}% ({level})\nValues: {data}"
    )
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8"),
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            result = json.loads(r.read().decode("utf-8"))
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Gemini error:", e)
        return fallback


# ---------- Routes ----------
@app.get("/")
def home():
    return {"status": "running"}


@app.get("/debug")
def debug():
    return {"model_type": type(model).__name__, "columns": columns}


@app.post("/predict")
def predict(patient: PatientData):
    try:
        data = patient.model_dump()

        missing = [c for c in columns if c not in data]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Model needs these columns that the form does not send: {missing}",
            )

        df = pd.DataFrame([data])[columns]
        prob = float(model.predict_proba(df)[0][1])
        risk_percent = round(prob * 100, 1)

        if risk_percent < 35:
            level = "LOW"
        elif risk_percent < 65:
            level = "MEDIUM"
        else:
            level = "HIGH"

        return {
            "risk_percent": risk_percent,
            "risk_level": level,
            "explanation": explain_with_gemini(data, risk_percent, level),
            "disclaimer": "This is a screening aid, not a medical diagnosis. Please consult a doctor.",
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")