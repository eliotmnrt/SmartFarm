import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.interpolate import Rbf  # Pour l'interpolation spatiale fluide

# ==========================================
# 1. CONFIGURATION DE LA GRILLE
# ==========================================
np.random.seed(42)
GRID_SIZE_X = 100  # Taille du champ en mètres
GRID_SIZE_Y = 100
N_CLUSTERS = 10    # Nombre de capteurs

rows = 2
cols = 5
cell_w = GRID_SIZE_X / cols
cell_h = GRID_SIZE_Y / rows

cluster_coords = {}
idx = 0

print("📍 Calcul des positions optimales des capteurs...")

for r in range(rows):
    for c in range(cols):
        if idx >= N_CLUSTERS: break
        
        # 1. Trouver le centre théorique de la case
        center_x = (c * cell_w) + (cell_w / 2)
        center_y = (r * cell_h) + (cell_h / 2)
        
        # 2. Ajouter un petit "Jitter" (bruit) pour le réalisme
        # Le capteur peut être décalé de ±8m autour du centre
        # Ça évite l'effet "robotique" trop parfait
        final_x = center_x + np.random.uniform(-8, 8)
        final_y = center_y + np.random.uniform(-8, 8)
        
        # Bornage pour rester dans le champ
        final_x = np.clip(final_x, 0, GRID_SIZE_X)
        final_y = np.clip(final_y, 0, GRID_SIZE_Y)
        
        cluster_id = f'cluster_{idx+1:02d}'
        cluster_coords[cluster_id] = (final_x, final_y)
        print(f"   - {cluster_id}: ({final_x:.1f}, {final_y:.1f}) [Zone {r+1}-{c+1}]")
        idx += 1

# ==========================================
# 2. DÉFINITION DES POINTS FORCÉS (ANCHORS)
# ==========================================
# C'est ici que vous dessinez votre carte de chaleur "logique".
# Format: (x, y): {'valeur_ref_moyenne': float}
# Les autres capteurs s'interpoleront entre ces points.

# SCÉNARIO : Une zone sèche en haut à gauche, une zone humide en bas à droite
ANCHORS = {
    # Coin Haut-Gauche (Sec & Chaud)
    (10, 90): {
        'temp_offset': 2.0,      # +2°C par rapport à la moyenne
        'hum_sol_offset': -10.0, # -10% d'humidité (Sec)
        'N_offset': -15.0        # Pauvre en Azote
    },
    # Coin Bas-Droit (Frais & Humide)
    (90, 10): {
        'temp_offset': -1.5,     # -1.5°C
        'hum_sol_offset': 10.0,  # +10% d'humidité (Humide)
        'N_offset': 10.0         # Riche en Azote
    },
    # Centre (Neutre)
    (50, 50): {
        'temp_offset': 0.0,
        'hum_sol_offset': 0.0,
        'N_offset': 0.0
    }
}

# ==========================================
# 3. GÉNÉRATION TEMPORELLE (Base Cycle)
# ==========================================
start_date = datetime(2025, 12, 10, 0, 0, 0)
duration_days = 4
samples_per_day = 48
total_samples = duration_days * samples_per_day
timestamps = [start_date + timedelta(minutes=30*i) for i in range(total_samples)]
hours = np.arange(total_samples) / 2

# Fonction générique pour interpoler une valeur à une position (x,y)
def get_spatial_offset(target_x, target_y, parameter):
    """
    Calcule le décalage (offset) pour un point donné en fonction des ancres.
    Utilise une pondération inverse à la distance (IDW simple).
    """
    numerator = 0
    denominator = 0
    
    for (ax, ay), offsets in ANCHORS.items():
        # Distance euclidienne
        dist = np.sqrt((target_x - ax)**2 + (target_y - ay)**2) + 0.1 # +0.1 éviter div/0
        weight = 1 / (dist ** 2) # Poids décroit avec le carré de la distance
        
        # Si le paramètre n'est pas défini pour l'ancre, on suppose 0 (neutre)
        val = offsets.get(parameter, 0.0)
        
        numerator += val * weight
        denominator += weight
        
    return numerator / denominator

# ==========================================
# 4. GÉNÉRATION DES DONNÉES
# ==========================================
all_data = []

# Base temporelle (Cycle Jour/Nuit standard)
base_temp_cycle = 20 + 8 * np.sin(2*np.pi*(hours/24) - np.pi/2)
base_hum_sol_cycle = 60 - (hours * 0.05) # Séchage lent naturel
base_n_cycle = 135 - (hours * 0.01)

print("Génération des données spatialisées...")

for cluster_id, (cx, cy) in cluster_coords.items():
    # 1. Calculer les "Personnalités" locales du cluster via interpolation
    local_temp_offset = get_spatial_offset(cx, cy, 'temp_offset')
    local_hum_sol_offset = get_spatial_offset(cx, cy, 'hum_sol_offset')
    local_n_offset = get_spatial_offset(cx, cy, 'N_offset')
    
    # 2. Générer les séries temporelles en appliquant ces offsets
    # On ajoute du bruit aléatoire pour que ce ne soit pas trop parfait
    
    # Température
    temp_ambient = base_temp_cycle + local_temp_offset + np.random.normal(0, 0.5, total_samples)
    temp_soil = np.convolve(temp_ambient, np.ones(5)/5, mode='same') # Inertie thermique
    
    # Humidité
    # L'humidité ambiante varie peu spatialement (l'air circule), mais le sol oui
    hum_ambient = 65 - 20 * np.sin(2*np.pi*(hours/24) - np.pi/2) + np.random.normal(0, 2, total_samples)
    hum_soil = base_hum_sol_cycle + local_hum_sol_offset + np.random.normal(0, 1.0, total_samples)
    hum_soil = np.clip(hum_soil, 0, 100) # Bornage 0-100%
    
    # Nutriments (Azote N, Phosphore P, Potassium K)
    # On suppose que P et K suivent une logique similaire à N pour simplifier
    n_val = base_n_cycle + local_n_offset + np.random.normal(0, 1, total_samples)
    p_val = 30 + (local_n_offset * 0.2) + np.random.normal(0, 0.5, total_samples) # Corrélation légère
    k_val = 200 + (local_n_offset * 0.5) + np.random.normal(0, 2, total_samples)
    
    ph_val = 6.8 + (local_hum_sol_offset * 0.01) + np.random.normal(0, 0.05, total_samples) # Sol humide souvent plus acide/basique selon contexte

    # Création du DataFrame pour ce cluster
    df_cluster = pd.DataFrame({
        'cluster_id': cluster_id,
        'timestamp': timestamps,
        'x': round(cx, 1), # On garde la coordonnée pour la visualisation
        'y': round(cy, 1),
        'temperature': temp_ambient.round(1),
        'soilTemperature': temp_soil.round(1),
        'humidity': hum_ambient.round(1),
        'soilMoisture': hum_soil.round(1),
        'azote_mg_kg': n_val.round(1),
        'phosphore_mg_kg': p_val.round(1),
        'potassium_mg_kg': k_val.round(1),
        'ph': ph_val.round(2)
    })
    
    all_data.append(df_cluster)

# Fusion finale
df_final = pd.concat(all_data, ignore_index=True)
df_final = df_final.sort_values(['timestamp', 'cluster_id'])

# Export
filename = 'donnees_spatiales_cluster.csv'
df_final.to_csv(filename, index=False)

print(f"✅ Terminé ! Fichier '{filename}' généré.")
print("\n--- Aperçu des offsets spatiaux calculés (Moyenne sur la période) ---")
summary = df_final.groupby(['cluster_id', 'x', 'y'])[['temperature', 'soilMoisture', 'azote_mg_kg']].mean().reset_index()
print(summary)

# ==========================================
# 5. VISUALISATION (AJOUT)
# ==========================================
import plotly.express as px

print("📊 Génération de la visualisation interactive...")

# Conversion du timestamp en texte pour que Plotly le lise comme une séquence
df_final['date_str'] = df_final['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

# Création du graphique animé
fig = px.scatter(
    df_final, 
    x='x', 
    y='y', 
    animation_frame='date_str',    # C'est ça qui crée la barre de progression (Slider)
    animation_group='cluster_id',  # Pour suivre les points d'une image à l'autre
    color='soilMoisture',        # La couleur change avec l'humidité
    size='temperature', # La taille change avec la température (optionnel)
    hover_name='cluster_id',       # Affiche le nom "cluster_XX" au survol
    hover_data=['azote_mg_kg', 'ph'], # Affiche les détails au survol
    
    # Esthétique
    range_x=[-5, 105], # On fixe les marges de la carte
    range_y=[-5, 105],
    range_color=[30, 90], # Fixe l'échelle de couleur (30% sec -> 90% humide)
    color_continuous_scale='RdYlBu', # Rouge (Sec) -> Bleu (Humide)
    title="Évolution Spatio-Temporelle du Champ (Humidité Sol)",
    template='plotly_dark'
)

# Force les points à être un peu plus gros
fig.update_traces(marker=dict(size=15))

# Affiche le résultat dans le navigateur
fig.show()

print("✅ Graphique ouvert dans le navigateur et sauvegardé sous 'simulation_champ.html'")