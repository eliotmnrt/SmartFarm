import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import joblib

# 1. Chargement
df = pd.read_csv('donnees_spatiales_cluster.csv')
model = joblib.load('field_state_model_full.pkl')
scaler = joblib.load('field_scaler_full.pkl')

# 2. On refait la prédiction pour avoir les couleurs
features = [
    'temperature', 'soilTemperature',
    'humidity', 'soilMoisture'
]
X = df[features]
X_scaled = scaler.transform(X)
df['cluster'] = model.predict(X_scaled)

# ========================================================
# VUE 1 : CLIMAT (Air)
# ========================================================
plt.figure(figsize=(10, 6))
sns.scatterplot(
    x='temperature', 
    y='humidity', 
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
    x='soilTemperature', 
    y='soilMoisture', 
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