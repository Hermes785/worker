# Utiliser une image Alpine avec les dépendances système nécessaires
FROM python:3.11-alpine

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apk add --no-cache \
    gcc \
    g++ \
    cmake \
    make \
    python3-dev \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    libjpeg \
    tiff \
    libpng \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev \
    libwebp-dev \
    libffi-dev

# Copier le fichier requirements.txt dans l'image
COPY requirements.txt /app/

# Créer un environnement virtuel et installer les dépendances
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# Copier tout le code dans l'image
COPY . /app/

# Spécifier que le conteneur utilisera le venv
ENV PATH="/venv/bin:$PATH"

# Définir la commande par défaut
CMD ["python", "worker.py"]
