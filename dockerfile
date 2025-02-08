# Utiliser une image Alpine avec les dépendances système nécessaires
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    cmake \
    make \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libwebp-dev \
    libffi-dev \
    tk-dev \
    tcl-dev \
    && rm -rf /var/lib/apt/lists/*



# Copier le fichier requirements.txt dans l'image
COPY requirements.txt ./
RUN pip install --no-cache-dir pymupdf python-docx numpy minio opencv-python-headless kafka-python kafka fontTools && pip install mysql-connector-python --no-cache-dir -r requirements.txt


# Copier tout le code dans l'image

COPY . /app/


RUN chmod +x /app/worker.py

RUN ls -l /app

EXPOSE 5000


# Définir la commande par défaut
CMD ["python", "worker.py"]
