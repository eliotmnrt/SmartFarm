import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import joblib

# 1. Chargement
df = pd.read_csv('donnees_10_clusters_4jours.csv')
model = joblib.load('field_state_model_full.pkl')
scaler = joblib.load('field_scaler_full.pkl')

# 2. On refait la prédiction pour avoir les couleurs
features = [
    'temperature_ambiante_c', 'temperature_sol_c',
    'humidite_ambiante', 'humidite_sol',
    'azote_mg_kg', 'phosphore_mg_kg', 'potassium_mg_kg', 'ph'
]
X = df[features]
X_scaled = scaler.transform(X)
df['cluster'] = model.predict(X_scaled)

# ========================================================
# VUE 1 : CLIMAT (Air)
# ========================================================
plt.figure(figsize=(10, 6))
sns.scatterplot(
    x='temperature_ambiante_c', 
    y='humidite_ambiante', 
    hue='cluster', 
    data=df, 
    palette='viridis', s=50, alpha=0.6
)
plt.title('Clusters selon le Climat (Air)')
plt.xlabel('Température Ambiante (°C)')
plt.ylabel('Humidité Ambiante (%)')
plt.grid(True, linestyle='--', alpha=0.3)
plt.legend(title='État (Cluster)', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# ========================================================
# VUE 2 : SOL (Eau vs Température)
# ========================================================
plt.figure(figsize=(10, 6))
sns.scatterplot(
    x='temperature_sol_c', 
    y='humidite_sol', 
    hue='cluster', 
    data=df, 
    palette='magma', s=50, alpha=0.6
)
plt.title('Clusters selon l\'État du Sol')
plt.xlabel('Température Sol (°C)')
plt.ylabel('Humidité Sol (%)')
plt.grid(True, linestyle='--', alpha=0.3)
plt.legend(title='État (Cluster)', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()