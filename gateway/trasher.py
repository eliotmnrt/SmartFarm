import pandas as pd
import numpy as np
import random

INPUT_FILE = '../docker/serviceIA/donnees_spatiales_cluster.csv'
OUTPUT_FILE = 'sensor_data_raw_dirty.csv'

# Probabilités (0.05 = 5% de chance)
PROB_OUTLIER = 0.02   # Valeur extrême
PROB_MISSING = 0.03   # Valeur manquante (NaN)
PROB_FREEZE = 0.05    # Capteur bloqué (répète la valeur précédente)


def introduce_chaos(df):
    df_dirty = df.copy()
    
    if 'x' in df_dirty.columns:
        df_dirty = df_dirty.drop(columns=['x'])
    if 'y' in df_dirty.columns:
        df_dirty = df_dirty.drop(columns=['y'])
    
    
    # Colonnes numériques à perturber
    sensor_cols = [
        'temperature', 'soilTemperature', 'humidity', 'soilMoisture', 
        'azote_mg_kg', 'phosphore_mg_kg', 'potassium_mg_kg', 'ph'
    ]
    
    # Adapter les noms de colonnes si votre CSV utilise les anciens noms
    # Mapping rapide au cas où
    actual_cols = [c for c in sensor_cols if c in df.columns]
    
    print("--- 1. Ajout de Bruit de fond (Léger) ---")
    for col in actual_cols:
        # Bruit normal (Sigma variable selon la colonne)
        noise_level = df[col].std() * 0.1 # 10% de l'écart type
        noise = np.random.normal(0, noise_level, size=len(df))
        df_dirty[col] += noise

    print("--- 2. Injection d'Anomalies ---")
    for i in range(len(df_dirty)):
        # On parcourt chaque ligne
        for col in actual_cols:
            dice = random.random()
            
            # A. Valeur Aberrante (Outlier)
            if dice < PROB_OUTLIER:
                # Soit negatif, soit tres grand, soit tres petit
                factor = random.choice([-1, 0.2, 5])
                print(f"factor: {factor}")
                print(f"⚠️ Outlier injecté à l'index {i}, colonne {col}")
                df_dirty.at[i, col] = df_dirty.at[i, col] * factor
            
            # B. Donnée manquante
            elif dice < PROB_OUTLIER + PROB_MISSING:
                df_dirty.at[i, col] = np.nan

    print("--- 3. Simulation Capteurs Bloqués (Freeze) ---")
    # On choisit un cluster au hasard qui va "bugger" a un moment donné
    broken_cluster = random.choice(df['cluster_id'].unique())
    bugged_col = random.choice(actual_cols)
    timestampStop = random.choice(df_dirty['timestamp'].unique())
    print(f"⚠️ Le capteur {broken_cluster} a buggé sur la colonne {bugged_col} à partir de {timestampStop}")

    freeze_value = None
    for i in range(len(df_dirty)):
        row = df_dirty.iloc[i]
        if row['cluster_id'] == broken_cluster and row['timestamp'] >= timestampStop:
            if freeze_value is None:
                freeze_value = row[bugged_col]
                print(f"   ❄️ Valeur gelée initiale: {freeze_value}")
            df_dirty.at[i, bugged_col] = freeze_value
    return df_dirty

# Exécution
try:
    df = pd.read_csv(INPUT_FILE)
    
    df_out = introduce_chaos(df)
    
    # Arrondir pour faire "vrai capteur"
    df_out = df_out.round(2)
    
    df_out.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Fichier bruité généré : {OUTPUT_FILE}")
    print(df_out.head(10))

except FileNotFoundError:
    print(f"❌ Erreur: Le fichier {INPUT_FILE} n'existe pas. Créez-le d'abord.")