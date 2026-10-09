import os
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
from typing import Optional,List, Dict, Any
from lime.lime_tabular import LimeTabularExplainer
from fastapi.responses import HTMLResponse
import matplotlib.pyplot as plt
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Crop Prediction API")
# ✅ ZID HNA: CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # تقدر تبدلها بـ ['http://localhost:3000'] ولا دومين تاعك
    allow_credentials=True,
    allow_methods=["*"],  # يسمح بكل الميثودات (POST, GET, OPTIONS ...)
    allow_headers=["*"],  # يسمح بكل الهيدرز (Content-Type, Authorization ...)
)

# --------- Models Loader ---------
def load_models(models_dir: str = 'models') -> Optional[dict]:
    try:
        return {
            'humidity_model': joblib.load(os.path.join(models_dir, 'humidity_model.pkl')),
            'crop_model': joblib.load(os.path.join(models_dir, 'crop_prediction_model.pkl')),
            'column_transformer': joblib.load(os.path.join(models_dir, 'column_transformer.pkl')),
            'scaler': joblib.load(os.path.join(models_dir, 'standard_scaler.pkl')),
            'label_encoder': joblib.load(os.path.join(models_dir, 'label_encoder.pkl')),
        }
    except FileNotFoundError as e:
        print(f"[ERROR] Loading models: {e}")
        return None


models = load_models()
if not models:
    raise RuntimeError("Failed to load models. Ensure model files exist in the specified directory.")

# Load training data for LIME explainer (if not available, will be created from dummy data)
try:
    X_train = joblib.load(os.path.join('models', 'X_train.pkl'))
    feature_names = joblib.load(os.path.join('models', 'feature_names.pkl'))
except FileNotFoundError:
    # Use dummy data if training data not available
    print("[WARNING] Training data not found. Using dummy data for LIME explainer.")
    dummy_data = np.random.rand(100, 11)  # Adjust the number of features as needed
    X_train = dummy_data
    feature_names = ['N', 'P', 'K', 'temperature', 'rainfall', 'ph', 
                    'State_Name', 'Crop_Type', 'Area_in_hectares', 
                    'Production_in_tons', 'Yield_ton_per_hec']

# --------- Input Schema ---------
class CropFeatures(BaseModel):
    N: float
    P: float
    K: float
    temperature: float
    rainfall: float
    ph: float
    State_Name: str
    Crop_Type: str
    Area_in_hectares: float
    Production_in_tons: float
    Yield_ton_per_hec: float
    Humidity_calculated: Optional[float] = None


# --------- Crop Prediction Logic ---------
def predict_crop(features: CropFeatures, models: dict) -> dict:
    features_dict = features.dict()
    features_df = pd.DataFrame([features_dict])
    
    if features.Humidity_calculated is None:
        humidity_features = features_df[['N', 'P', 'K', 'rainfall', 'temperature', 'ph']]
        humidity = models['humidity_model'].predict(humidity_features)[0]
        features_df['Humidity_calculated'] = humidity
    else:
        humidity = features.Humidity_calculated
    
    X = models['column_transformer'].transform(features_df)
    X = models['scaler'].transform(X)
    
    crop_id = models['crop_model'].predict(X)[0]
    crop_name = models['label_encoder'].inverse_transform([crop_id])[0]
    
    confidence = 0.0
    if hasattr(models['crop_model'], 'predict_proba'):
        probabilities = models['crop_model'].predict_proba(X)[0]
        confidence = probabilities[crop_id]
    
    return {
        "predicted_crop": crop_name,
        "confidence": float(confidence),
        "humidity_calculated": float(humidity)
    }




# --------- API Routes ---------
@app.post("/predict", summary="Predict Crop Type")
def predict(features: CropFeatures):
    try:
        result = predict_crop(features, models)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from dzLime.lime import explain_with_lime_api
import json

@app.post("/explain", summary="Explain Crop Prediction using LIME")
def explain(features: CropFeatures):
    try:
        features_dict = features.dict()
        features_df = pd.DataFrame([features_dict])
        # Calculate humidity if not provided
        if features.Humidity_calculated is None:
            humidity_features = features_df[['N', 'P', 'K', 'rainfall', 'temperature', 'ph']]
            humidity = models['humidity_model'].predict(humidity_features)[0]
            features_df['Humidity_calculated'] = humidity
        
        # Generate explanation
        explanation = explain_with_lime_api(features_df, models,X_train)
        result = json.loads(explanation)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/explain-html/{crop_id}", response_class=HTMLResponse)
def explain_html(crop_id: int):

    """
    Return an HTML visualization of the LIME explanation
    """
    try:
        # This would be expanded to include actual data if crop_id were to 
        # reference a real database entry
        return f"""
        <html>
            <head>
                <title>Crop Prediction Explanation</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    h1 {{ color: green; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Crop Prediction Explanation</h1>
                    <p>To generate an explanation, use the /explain endpoint with your crop data.</p>
                </div>
            </body>
        </html>
        """
    except Exception as e:
        return f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error</h1>
                <p>{str(e)}</p>
            </body>
        </html>
        """
    


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse("index.html") 

from fastapi.staticfiles import StaticFiles

# static files from root (hacky but works)
app.mount("/", StaticFiles(directory="."), name="static")
