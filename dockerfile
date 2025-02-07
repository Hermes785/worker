# Utiliser une image officielle de Python
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

RUN pip install pymupdf

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port that the Flask app will run on
EXPOSE 5000

# Set the command to run the Flask app
CMD ["python", "worker.py"]
