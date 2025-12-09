import pandas as pd
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# 1. Chargement
df = pd.read_csv('donnees_10_clusters_4jours.csv')

# 2. On sélectionne TOUTES les données numériques (Les "Sensors")
# On laisse tomber 'cluster_id' (texte) et 'timestamp' (date)
features = [
    'temperature_ambiante_c', 
    'temperature_sol_c',       # Ajouté
    'humidite_ambiante',     # Ajouté
    'humidite_sol', 
    'azote_mg_kg', 
    'phosphore_mg_kg',         # Ajouté
    'potassium_mg_kg',         # Ajouté
    'ph'
]

X = df[features]

# 3. Normalisation (Toujours obligatoire avec K-Means)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Entraînement (K-Means)
# Avec plus de données, on peut peut-être distinguer plus d'états (ex: 4)
kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
kmeans.fit(X_scaled)

# 5. Sauvegarde
joblib.dump(kmeans, 'field_state_model_full.pkl')
joblib.dump(scaler, 'field_scaler_full.pkl')

print(f"✅ Modèle entraîné avec {len(features)} capteurs !")
print("Centres des clusters (Moyennes par état) :")
print(pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), columns=features))