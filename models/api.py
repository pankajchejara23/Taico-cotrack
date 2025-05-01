from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import json
from typing import List
import pandas as pd

app = FastAPI(title="RandomForest Prediction API",
              description="API for making predictions with trained RandomForest model")

# Load model and feature names
cq_model = joblib.load("./random_forest_CQ.joblib")
arg_model = joblib.load("./random_forest_ARG.joblib")
smu_model = joblib.load("./random_forest_SMU.joblib")
str_model = joblib.load("./random_forest_STR.joblib")

models = {'collaboration quality':cq_model,'argumentation':arg_model,'smu_model':smu_model,'str_model':str_model}


# Feature names
with open("./feature_columns.json", "r") as f:
    REQUIRED_FEATURES = json.load(f)

class PredictionInput(BaseModel):
    user_add_mean: float
    user_del_mean: float
    user_speak_mean: float
    user_turns_mean: float
    user_wh_mean: float
    user_self_mean: float
    user_us_mean: float
    user_add_sd: float
    user_del_sd: float
    user_speak_sd: float
    user_turns_sd: float
    user_wh_sd: float
    user_self_sd: float
    user_us_sd: float
    
class PredictionOutput(BaseModel):
    prediction: int
    probability: float
    version: str

@app.post("/predict/")
async def predict_cq(input_data: PredictionInput):
    """Make predictions with the RandomForest model"""
    try:
        features_dict = input_data.dict()
        print('Features:',features_dict)
        
        # Ensure the features are in the correct order as expected by the model
        ordered_features = [features_dict[feature] for feature in REQUIRED_FEATURES]
        test_x = pd.DataFrame(features_dict, index=[0])
            
        response = {}  
        # Make predictions
        for target, model in models.items():
            prediction = int(model.predict(test_x)[0])  # Get first prediction
            probability = float(model.predict_proba(test_x)[0, 1])  # Get probability for class 1
            response[target] = {'prediction':prediction, 'probability':probability}
        
        print('Prediction:',response)
        return response
        
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.get("/model_info")
async def model_info():
    """Return model metadata"""
    return {
        "model_type": "RandomForestClassifier",
        "n_features": len(REQUIRED_FEATURES),
        "features": REQUIRED_FEATURES,
        "parameters": model.get_params()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)