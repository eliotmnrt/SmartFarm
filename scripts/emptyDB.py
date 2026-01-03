import requests
import json

# --- CONFIGURATION ---
CRATEDB_SQL_URL = "http://localhost:4200/_sql"
ORION_URL = "http://localhost:1026/v2/entities"

# Headers FIWARE (Identiques à ceux utilisés pour l'envoi)
FIWARE_HEADERS = {
    'fiware-service': 'openiot',
    'fiware-servicepath': '/'
}

def clear_history_cratedb():
    print("🗑️  Nettoyage de l'historique CrateDB...")
    
    # Liste des tables probables (basé sur tes types d'entités)
    # QuantumLeap crée des tables au format "schema"."etType"
    tables_to_drop = [
        '"mtopeniot"."etdevice"',   # Table des devices/capteurs
        '"mtopeniot"."etcluster"',  # Table des clusters
    ]

    for table in tables_to_drop:
        payload = {"stmt": f"DELETE FROM {table};"}        
        try:
            r = requests.post(CRATEDB_SQL_URL, json=payload)
            if r.status_code == 200:
                print(f"   ✅ Table {table} vidée (ou n'existait pas).")
            else:
                print(f"   ⚠️ Erreur sur {table}: {r.text}")
        except Exception as e:
            print(f"   ❌ Erreur connexion CrateDB: {e}")

def clear_context_orion():
    print("\n🗑️  Nettoyage des entités Orion (Temps réel)...")
    
    try:
        # 1. Récupérer la liste de toutes les entités
        # limit=1000 pour être sûr de tout prendre
        r = requests.get(f"{ORION_URL}?limit=1000", headers=FIWARE_HEADERS)
        entities = r.json()
        
        if not entities:
            print("   ℹ️  Aucune entité trouvée dans Orion.")
            return

        print(f"   Détection de {len(entities)} entités à supprimer...")

        # 2. Supprimer une par une
        count = 0
        for entity in entities:
            entity_id = entity['id']
            # delete=true force la suppression même si références
            del_url = f"{ORION_URL}/{entity_id}?type={entity['type']}"
            
            resp = requests.delete(del_url, headers=FIWARE_HEADERS)
            if resp.status_code == 204:
                count += 1
                print(f"   💀 Deleted: {entity_id}", end='\r') 
            else:
                print(f"   ❌ Échec: {entity_id} ({resp.status_code})")
        
        print(f"\n   ✅ {count} entités supprimées avec succès.")

    except Exception as e:
        print(f"   ❌ Erreur connexion Orion: {e}")

if __name__ == "__main__":
    print("⚠️  ATTENTION : Ceci va supprimer TOUTES les données (Hist & Live).")
    confirm = input("Appuyez sur ENTER pour confirmer (ou CTRL+C pour annuler)...")
    
    clear_history_cratedb()
    clear_context_orion()
    
    print("\n✅ Nettoyage terminé.")