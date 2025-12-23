import joblib
import numpy as np
from fastapi import FastAPI, Request, HTTPException
import httpx
import uvicorn
import pandas as pd
from typing import Dict, Any



app = FastAPI(title="Smart Field AI Service")

# Chargement des modèles
print("Chargement des modèles...")
model = joblib.load('field_state_model_full.pkl')
scaler = joblib.load('field_scaler_full.pkl')

ORION_URL = "http://orion:1026"
HEADERS = {
    "fiware-service": "openiot",
    "fiware-servicepath": "/"
}

STATE_LABELS = {
    0: "Sec & Chaud",
    1: "Frais & Humide",
    2: "Standard" 
}

async def update_orion_entity(entity_id: str, attributes: Dict[str, Any]) -> bool:
    """Mise à jour d'une entité Orion avec retry"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{ORION_URL}/v2/entities/{entity_id}/attrs",
                json=attributes,
                headers=HEADERS
            )
            print(response.status_code, response.text)
            
            if response.status_code in [204, 200]:
                print(f"✅ Orion mis à jour pour {entity_id}")
                return True
            else:
                print(f"❌ Orion erreur {response.status_code}: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print(f"⏱️ Timeout lors de la mise à jour de {entity_id}")
        return False
    except Exception as e:
        print(f"❌ Erreur Orion pour {entity_id}: {e}")
        return False

@app.post("/v2/notify")
async def receive_notification(request: Request):
    """Endpoint de notification NGSI-v2"""
    processed = 0
    errors = 0
    
    try:
        body = await request.json()
        data_list = body.get("data", [])
        
        print(f"🔔 Notification reçue avec {len(data_list)} entités")

        for entity in data_list:
            entity_id = entity.get("id")
            if not entity_id:
                print("❌ Entité sans ID")
                errors += 1
                continue
                
            print(f"🔮 Analyse de {entity_id}...")

            try:
                # Extraction des features
                features = {
                    'temperature': float(entity["temperature"]["value"]),
                    'soilTemperature': float(entity["soilTemperature"]["value"]),
                    'humidity': float(entity["humidity"]["value"]),
                    'soilMoisture': float(entity["soilMoisture"]["value"]),
                }
                print(f"   📊 Features: {features}")
                
            except (KeyError, ValueError, TypeError) as e:
                print(f"❌ Données invalides pour {entity_id}: {e}")
                errors += 1
                continue

            # Prédiction
            try:
                features_df = pd.DataFrame([features])
                features_scaled = scaler.transform(features_df)
                cluster_state = int(model.predict(features_scaled)[0])
                
                state_desc = STATE_LABELS.get(cluster_state, "Inconnu")
                print(f"✅ Prédiction: {entity_id}, état {cluster_state} → {state_desc}")
                
            except Exception as e:
                print(f"❌ Erreur de prédiction pour {entity_id}: {e}")
                errors += 1
                continue

            # Mise à jour Orion
            payload = {
                "fieldState": {
                    "value": cluster_state,
                    "type": "Integer",
                    "metadata": {
                        "timestamp": {
                            "type": "DateTime",
                            "value": pd.Timestamp.now().isoformat()
                        }
                    }
                },
                "clusterId": {
                    "value": entity_id,
                    "type": "String"
                }
            }

            print(payload)
            success = await update_orion_entity(entity_id, payload)
            if success:
                processed += 1
            else:
                errors += 1

        return {
            "status": "completed",
            "processed": processed,
            "errors": errors,
            "total": len(data_list)
        }
        
    except Exception as e:
        print(f"💥 Erreur critique: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Field Analyzer",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)