from pdf2docx import Converter
import json
from kafka import KafkaConsumer
from minio import Minio
import mysql.connector
from datetime import timedelta
import fitz  # PyMuPDF
from PIL import Image
import io

# Initialisation du client MinIO
minio_client = Minio(
    "play.min.io",
    region="us-east-1",
    access_key="Q3AM3UQ867SPQQA43P2F",
    secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG"
)

# Fonction pour télécharger le fichier PDF depuis MinIO
def minioDOwloadFileService(message):
    try:
        data = json.loads(message)  
        bucket_Name = data.get("bucket_Name")
        file_name = data.get("file_name")
        file_path = data.get("file_path")
        requestId = data.get("requestId")

        if not file_name or not file_path:
            print("Erreur : Nom de fichier ou chemin manquant dans le message Kafka.")
            return None
      
        local_file_path = f"./tmp/{file_name}"
        minio_client.fget_object(bucket_Name, file_name, local_file_path)
        print(f"Fichier {file_name} téléchargé avec succès depuis MinIO.")
       
        return local_file_path, bucket_Name, requestId
    
    except Exception as e:
        print(f"Erreur lors du téléchargement du fichier : {e}")
        return None

# Fonction pour convertir les images en RGB pour éviter l'erreur
def fix_pdf_images(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            img_list = doc[page_num].get_images(full=True)
            for img_index, img in enumerate(img_list):
                xref = img[0]  # ID de l'image dans le document
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                img_ext = base_image["ext"]

                # Convertir seulement si l'image n'est pas en RGB
                img_pil = Image.open(io.BytesIO(img_bytes))
                if img_pil.mode not in ("RGB", "L"):  # RGB ou niveaux de gris OK
                    img_pil = img_pil.convert("RGB")
                    img_pil_bytes = io.BytesIO()
                    img_pil.save(img_pil_bytes, format="PNG")
                    img_bytes = img_pil_bytes.getvalue()

                    # Remplace l'image originale par la nouvelle version compatible
                    doc.update_image(xref, stream=img_bytes)

        # Sauvegarde un nouveau PDF propre
        fixed_pdf_path = pdf_path.replace(".pdf", "_fixed.pdf")
        doc.save(fixed_pdf_path)
        doc.close()
        print("Images du PDF corrigées avec succès.")
        return fixed_pdf_path
    except Exception as e:
        print(f"Erreur lors de la correction des images du PDF : {e}")
        return pdf_path  # Retourne le PDF original si la correction échoue
    

# Fonction pour uploader le fichier Word converti sur MinIO
def minioUploadDocsFile(bucket_Name, source_file, destination_file):
    try:
        minio_client.fput_object(bucket_Name, destination_file, source_file)
        print(f"{source_file} successfully uploaded as object {destination_file} to bucket {bucket_Name}")
    except Exception as e:
        print(f"Erreur lors de l'upload du fichier : {e}")
        return None

# Fonction pour générer un lien de téléchargement
def generateUrlFile(bucket_Name, destination_file):
    try:
        urlGenerated = minio_client.presigned_get_object(bucket_Name, destination_file, expires=timedelta(seconds=3600))
        print(f"URL généré pour le fichier {destination_file} : {urlGenerated}")  
        return urlGenerated      
    except Exception as ex:
        print(f"Erreur inattendue : {ex}")
        return False    

# Fonction pour enregistrer les informations dans MySQL
def sendToBD(requestId, bucket_Name, file_path, destination_file, urlGenerated):
    try:
        print("Tentative de connexion à la base de données MySQL...")
        mydb = mysql.connector.connect(
            host="mysql_db_worker",
            user="myuser",
            password="mypassword",
            connection_timeout=5,
        )
        mydb.autocommit = True
        print("Connexion établie.")
        mycursor = mydb.cursor()
        mycursor.execute("CREATE DATABASE IF NOT EXISTS file_convert")
        mycursor.execute("USE file_convert")
        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS file (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                requestId VARCHAR(255), 
                bucket_Name VARCHAR(255), 
                file_path VARCHAR(255), 
                filename VARCHAR(255), 
                urlGenerated VARCHAR(255)
            )
        """)
        sql = "INSERT INTO file (requestId, bucket_Name, file_path, filename, urlGenerated) VALUES(%s, %s, %s, %s, %s)"
        val = (requestId, bucket_Name, file_path, destination_file, urlGenerated)
        mycursor.execute(sql, val)
        mydb.commit()
        print("Données insérées avec succès.")
    except mysql.connector.Error as e:
        print(f"Erreur MySQL [{e.errno}]: {e.msg}")
        return False
    except Exception as ex:
        print(f"Erreur inattendue : {ex}")
        return False
    finally:
        try:
            if mycursor:
                mycursor.close()
            if mydb:
                mydb.close()
        except Exception as ex:
            print("Erreur lors de la fermeture de la connexion :", ex)

# Fonction principale pour consommer les messages Kafka
def kafkaService():
    consumer = KafkaConsumer(
        'files_to_convert',
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    print("Worker en attente de messages Kafka...")
    for message in consumer:
        print(f"Message reçu : {message.value.decode()}")

        pdf_path, bucket_Name, requestId = minioDOwloadFileService(message.value.decode())
        
        if pdf_path:
            # Correction des images pour éviter l'erreur
            fixed_pdf_path = fix_pdf_images(pdf_path)
        
            docx_path = fixed_pdf_path.replace(".pdf", ".docx")  
            file_path = docx_path

            cv = Converter(fixed_pdf_path)
            cv.convert(docx_path, start=0, end=None, extract_image=True, clip_image_res_ratio=1.0)
            print(f"Conversion terminée : {docx_path}")
            destination_file = docx_path.split("/")[-1]            

            minioUploadDocsFile(bucket_Name, docx_path, destination_file)
            urlGenerated = generateUrlFile(bucket_Name, destination_file)
            sendToBD(requestId, bucket_Name, file_path, destination_file, urlGenerated)

            cv.close()
        else:
            print("Le fichier n'a pas pu être téléchargé, conversion annulée.")

# Lancer le service Kafka
kafkaService()
