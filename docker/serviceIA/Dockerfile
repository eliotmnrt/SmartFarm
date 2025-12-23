FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copie du code ET des modèles (.pkl)
COPY main.py .
COPY field_state_model_full.pkl .
COPY field_scaler_full.pkl .

# Lancement
CMD ["python", "main.py"]