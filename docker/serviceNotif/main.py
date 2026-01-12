import os
import httpx
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from typing import Dict, Any

app = FastAPI(title="SmartFarm Notification Service")

# Configuration
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

SEND_DISCORD = os.getenv('SEND_DISCORD', 'true').lower() == 'true'
SEND_SMS = os.getenv('SEND_SMS', 'false').lower() == 'true'
SEND_EMAIL = os.getenv('SEND_EMAIL', 'false').lower() == 'true'

# --- MÉMOIRE DES ÉTATS (Pour éviter les doublons) ---
# Clé: entity_id, Valeur: dernier état connu (ex: "NO_IRRIGATION")
last_known_states: Dict[str, str] = {}


async def send_discord_notification(entity_id: str, field: str, value: str):
    """Envoie une notif sur Discord via Webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ Pas d'URL Discord configurée.")
        return

    print(f"🚀 Envoi Discord ({field}) pour {entity_id}...")
    
    # défaut
    embed_title = f"Notification : {entity_id}"
    field_name = "Valeur"
    color = 5763719 # Vert par défaut
    title_prefix = "Info"
    
    value_upper = value.upper()

    # --- CAS 1 : IRRIGATION ---
    if field == "irrig":
        is_alert = "NO_IRRIGATION" not in value_upper
        
        embed_title = f"💧 Alerte Irrigation : {entity_id}"
        field_name = "Recommandation"
        
        # Orange (Alerte) ou Vert (OK)
        color = 15105570 if is_alert else 5763719  
        title_prefix = "⚠️ Action Requise" if is_alert else "✅ Info"

    # --- CAS 2 : ÉTAT TECHNIQUE (STATE) ---
    elif field == "state":
        is_error = "ACTIVE" not in value_upper
        
        embed_title = f"🔧 État Technique : {entity_id}"
        field_name = "Statut du Cluster"
        
        if is_error:
            color = 15548997 # ROUGE (Discord Red) pour les erreurs (BROKEN, FREEZE)
            title_prefix = "🚨 Panne Détectée"
        else:
            color = 5763719 # VERT pour ACTIVE
            title_prefix = "✅ Retour à la normale"

    # --- CONSTRUCTION DE L'EMBED ---
    embed = {
        "title": embed_title,
        "description": f"**{title_prefix}** : Changement détecté.",
        "color": color,
        "fields": [
            {"name": field_name, "value": f"**{value}**", "inline": True},
            {"name": "Cluster ID", "value": entity_id, "inline": True}
        ],
        "footer": {"text": "SmartFarm Notification System"}
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
            if resp.status_code < 300:
                print(f"✅ Discord notifié pour {entity_id}")
            else:
                print(f"❌ Erreur Discord {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"❌ Exception Discord: {e}")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
            if resp.status_code < 300:
                print(f"✅ Discord notifié pour {entity_id}")
            else:
                print(f"❌ Erreur Discord {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"❌ Exception Discord: {e}")


async def send_email_notification(entity_id: str, field: str, value: str):
    """Placeholder pour l'envoi d'email"""
    print(f"📧 [Email - Simulation] Envoi à l'agriculteur pour {entity_id}: {value}")

async def send_sms_notification(entity_id: str, field: str, value: str):
    """Placeholder pour l'envoi de SMS"""
    print(f"📱 [SMS - Simulation] Envoi sur mobile pour {entity_id}: {value}")

async def dispatch_notifications(entity_id: str, field: str, value: str):
    """Orchestrateur : appelle tous les canaux activés"""
    if SEND_DISCORD:
        await send_discord_notification(entity_id, field, value)
    if SEND_EMAIL:
        await send_email_notification(entity_id, field, value)
    if SEND_SMS:    
        await send_sms_notification(entity_id, field, value)


@app.post("/v2/notify")
async def receive_notification(request: Request):
    """Endpoint reçu par Orion lors d'un changement"""
    try:
        body = await request.json()
        data_list = body.get("data", [])
        
        for entity in data_list:
            entity_id_full = entity.get("id", "unknown")
            entity_id = entity_id_full.split(':')[-1] 
            
            try:
                # Liste des attributs à surveiller : (Nom dans Orion, Type pour la notif)
                attributes_to_check = [
                    ("irrigationrecommendation", "irrig"),
                    ("state", "state")
                ]

                for attr_name, notif_type in attributes_to_check:
                    
                    # 1. Extraction générique de la valeur
                    attr_data = entity.get(attr_name, {})
                    
                    if isinstance(attr_data, dict):
                        raw_val = attr_data.get("value")
                    else:
                        raw_val = attr_data

                    new_value = str(raw_val) if raw_val is not None else "None"

                    # 2. Logique de dédoublonnage
                    if entity_id and new_value != "None":
                        memory_key = f"{entity_id}_{attr_name}"
                        
                        previous_value = last_known_states.get(memory_key)

                        if new_value != previous_value:
                            print(f"🔄 Changement [{attr_name}] pour {entity_id}: {previous_value} -> {new_value}")
                            
                            last_known_states[memory_key] = new_value
                            
                            await dispatch_notifications(entity_id, notif_type, new_value)
                        else:
                            pass
                    else:
                        print(f"⚠️ Donnée {attr_name} incomplète pour {entity_id}")

            except Exception as e:
                print(f"❌ Erreur lecture entité {entity_id}: {e}")

        return {"status": "processed"}
        
    except Exception as e:
        print(f"💥 Erreur critique: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Notification Service"}

# Ce bloc ne sert que pour le débug local (python main.py)
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)