# Utiliser une image officielle de Python
FROM python:alpine

# Set the working directory in the container
WORKDIR /app

RUN pip install pymupdf

RUN pip install python-docx


# Copy the requirements file into the container
COPY requirements.txt /app/


# Installer les dépendances dans un venv et mettre à jour pip proprement
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt
 RUN pip install --no-cache-dir numpy pdf2docx



# Copy the rest of the application code into the container
COPY . /app/



# Set the command to run the Flask app
CMD ["python", "worker.py"]
