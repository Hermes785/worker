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
COPY requirements.txt ./

# Copier tout le code dans l'image
COPY . /app/


RUN chmod +x /app/worker.py

RUN ls -l /app

EXPOSE 5000


# Définir la commande par défaut
CMD ["python", "worker.py"]
