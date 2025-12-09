import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Chargement du cerveau au démarrage
model = joblib.load('field_state_model.pkl')
scaler = joblib.load('field_scaler.pkl')

# Définition des noms d'états (basé sur notre analyse ci-dessus)
STATE_LABELS = {
    0: "⚠️ Risque Carence (Azote bas)",
    1: "🟢 Croissance Optimale",
    2: "🔵 Repos / Nuit"
}

# Modèle de données attendu en entrée
class SensorData(BaseModel):
    temperature_ambiante_c: float
    temperature_sol_c: float       # <--- Nouveau
    humidite_ambiante: float     # <--- Nouveau
    humidite_sol: float
    azote_mg_kg: float
    phosphore_mg_kg: float         # <--- Nouveau
    potassium_mg_kg: float         # <--- Nouveau
    ph: float

@app.post("/predict_state")
def predict_state(data: SensorData):
    # 1. Préparer les données
    # Attention: l'ordre doit être identique à l'entraînement !
    features = [[
        data.temperature_ambiante_c,
        data.temperature_sol_c,
        data.humidite_ambiante,
        data.humidite_sol,
        data.azote_mg_kg,
        data.phosphore_mg_kg,
        data.potassium_mg_kg,
        data.ph
    ]]
    
    # 2. Normaliser
    features_scaled = scaler.transform(features)
    
    # 3. Prédire le cluster (0, 1 ou 2)
    cluster_id = int(model.predict(features_scaled)[0])
    
    # 4. Renvoyer l'interprétation
    return {
        "state_id": cluster_id,
        "description": STATE_LABELS.get(cluster_id, "Inconnu"),
        "confidence": "Automated estimation via K-Means"
    }

# Pour lancer : uvicorn ai_service:app --reload