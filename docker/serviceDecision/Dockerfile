FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances
RUN pip install requests

# Copie du code
COPY main.py .

# Lancement
CMD ["python", "main.py"]