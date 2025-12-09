import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
np.random.seed(42)
start_date = datetime(2024, 1, 15, 0, 0, 0)
duration_days = 4
samples_per_day = 48
total_samples = duration_days * samples_per_day
n_clusters = 10

# Génération des timestamps
timestamps = [start_date + timedelta(minutes=30*i) for i in range(total_samples)]
hours_from_start = np.arange(total_samples) / 2

# Génération des valeurs de base (identiques pour tous les clusters)
def generate_base_values():
    base_temp = 20
    temp_ambient = base_temp + 8 * np.sin(2*np.pi*(hours_from_start/24) - np.pi/2) + np.random.normal(0, 1.5, total_samples)
    
    temp_soil = np.convolve(np.roll(temp_ambient, 6), np.ones(6)/6, mode='same') + np.random.normal(0, 0.5, total_samples)
    
    humidity_ambient = 65 - 20 * np.sin(2*np.pi*(hours_from_start/24) - np.pi/2) + np.random.normal(0, 3, total_samples)
    humidity_soil = 70 - (hours_from_start * 0.02/24) + 5 * np.sin(2*np.pi*(hours_from_start/24) - np.pi/2) + np.random.normal(0, 1.5, total_samples)
    
    days = hours_from_start / 24
    N = 135 - days * 1.2 + np.random.normal(0, 0.8, total_samples)
    P = 30 - days * 0.3 + np.random.normal(0, 0.2, total_samples)
    K = 200 - days * 1.8 + np.random.normal(0, 1.2, total_samples)
    
    ph = 6.8 + np.random.normal(0, 0.05, total_samples)
    
    return {
        'temperature_ambiante_c': temp_ambient,
        'temperature_sol_c': temp_soil,
        'humidite_ambiante': humidity_ambient,
        'humidite_sol': humidity_soil,
        'azote_mg_kg': N,
        'phosphore_mg_kg': P,
        'potassium_mg_kg': K,
        'ph': ph
    }

base_values = generate_base_values()

# Génération des biais par cluster (cohérents dans le temps)
cluster_biases = {}
for i in range(1, n_clusters + 1):
    cluster_biases[f'cluster_{i:02d}'] = {
        'temp_ambiante': np.random.normal(0, 0.8),  # Biais de ±2°C max
        'temp_sol': np.random.normal(0, 0.5),       # Biais de ±1.5°C max
        'humidite_ambiante': np.random.normal(0, 3), # Biais de ±8% max
        'humidite_sol': np.random.normal(0, 2),      # Biais de ±5% max
        'N': np.random.normal(0, 2),                # Biais de ±5 mg/kg
        'P': np.random.normal(0, 0.5),              # Biais de ±1.5 mg/kg
        'K': np.random.normal(0, 3),                # Biais de ±8 mg/kg
        'ph': np.random.normal(0, 0.08)             # Biais de ±0.2 pH
    }

# Création des données pour chaque cluster
all_data = []
for cluster_id, biases in cluster_biases.items():
    cluster_data = pd.DataFrame({
        'cluster_id': cluster_id,
        'timestamp': timestamps,
    })
    
    # Application des valeurs de base + biais du cluster
    for col, values in base_values.items():
        if 'temperature_ambiante' in col:
            cluster_data[col] = values + biases['temp_ambiante']
        elif 'temperature_sol' in col:
            cluster_data[col] = values + biases['temp_sol']
        elif 'humidite_ambiante' in col:
            cluster_data[col] = values + biases['humidite_ambiante']
        elif 'humidite_sol' in col:
            cluster_data[col] = values + biases['humidite_sol']
        elif col == 'azote_mg_kg':
            cluster_data[col] = values + biases['N']
        elif col == 'phosphore_mg_kg':
            cluster_data[col] = values + biases['P']
        elif col == 'potassium_mg_kg':
            cluster_data[col] = values + biases['K']
        elif col == 'ph':
            cluster_data[col] = values + biases['ph']
    
    all_data.append(cluster_data)

# Concaténation de tous les clusters
df_all = pd.concat(all_data, ignore_index=True)

# Arrondi et clipping pour rester dans des plausibles
df_all['temperature_ambiante_c'] = df_all['temperature_ambiante_c'].round(1)
df_all['temperature_sol_c'] = df_all['temperature_sol_c'].round(1)
df_all['humidite_ambiante'] = df_all['humidite_ambiante'].round(1)
df_all['humidite_sol'] = df_all['humidite_sol'].round(1)
df_all['azote_mg_kg'] = df_all['azote_mg_kg'].round(1)
df_all['phosphore_mg_kg'] = df_all['phosphore_mg_kg'].round(1)
df_all['potassium_mg_kg'] = df_all['potassium_mg_kg'].round(1)
df_all['ph'] = df_all['ph'].round(2)

# Tri par timestamp puis cluster_id
df_all = df_all.sort_values(['timestamp', 'cluster_id']).reset_index(drop=True)

# Export CSV
csv_filename = 'donnees_10_clusters_4jours.csv'
df_all.to_csv(csv_filename, index=False, date_format='%Y-%m-%d %H:%M:%S')

print(f"✅ {total_samples * n_clusters} relevés générés pour {n_clusters} clusters")
print(f"💾 Fichier sauvegardé : {csv_filename}")

# Statistiques par capteur
print("\n--- Biais par cluster (écart à la référence) ---")
stats = df_all.groupby('cluster_id').agg({
    'temperature_ambiante_c': 'mean',
    'humidite_sol': 'mean',
    'azote_mg_kg': 'mean',
    'ph': 'mean'
}).round(2)
print(stats)

# Aperçu
print("\n--- Aperçu des 3 premiers timestamps ---")
sample_timestamps = df_all['timestamp'].unique()[:3]
print(df_all[df_all['timestamp'].isin(sample_timestamps)].head(15).to_string(index=False))