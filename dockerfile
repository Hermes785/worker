# Utiliser une image officielle de Python
FROM python:3.11

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers du projet
COPY . .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exécuter le script principal au démarrage du conteneur
CMD ["python", "worker.py"]
