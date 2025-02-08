from pdf2docx import Converter
import json
from kafka import KafkaConsumer
from minio import Minio
import mysql.connector
from datetime import timedelta


# Initialisation du client MinIO une seule fois
minio_client = Minio(
    "play.min.io",
     region= "us-east-1",
    access_key="Q3AM3UQ867SPQQA43P2F",
    secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG"
)


# Fonction pour télécharger le fichier pdf a convertir  de MinIO
def minioDOwloadFileService(message):
    try:
        data = json.loads(message)  
        bucket_Name =data.get("bucket_Name")
        file_name = data.get("file_name")
        file_path = data.get("file_path")
        requestId= data.get("requestId")

        if not file_name or not file_path:
            print("Erreur : Nom de fichier ou chemin manquant dans le message Kafka.")
            return None
      
        local_file_path = f"./tmp/{file_name}"
        minio_client.fget_object(bucket_Name, file_name, local_file_path)
        print(f"Fichier {file_name} téléchargé avec succès depuis MinIO.")
       
     
        return local_file_path,bucket_Name,requestId
    
    except Exception as e:
        print(f"Erreur lors du téléchargement du fichier : {e}")
        return None
    
   # FOnction pour uploader le fichier pdf convertir en word sur minio 
def minioUploadDocsFile(bucket_Name,source_file,destination_file):
    try:
       
        minio_client.fput_object( bucket_Name, destination_file, source_file,)
        print(source_file, "successfully uploaded as object",destination_file, "to bucket", bucket_Name,)
     
    except Exception as e:
        print(f"Erreur lors de l'upload du fichier du fichier : {e}")
        return None
    
  # fonction pour la connection a la base de donnees  
def sendToBD(requestId,bucket_Name,file_path,destination_file,urlGenerated):
    try:
        mydb = mysql.connector.connect(
        host="mysql_db_worker",
        user="myuser",
        password="rootpassword")
        mycursor = mydb.cursor()
        mycursor.execute("CREATE DATABASE IF NOT EXISTS file_convert ")
        print("Base de données créée avec succès.")
        mycursor.execute("USE file_convert")
        mycursor.execute("CREATE TABLE IF NOT EXISTS  file (id INT AUTO_INCREMENT PRIMARY KEY,requestId VARCHAR(255), bucket_Name VARCHAR(255), file_path VARCHAR(255),filename VARCHAR(255),urlGenerated VARCHAR(255))")  
        print("Table créée avec succès.")
        sql = "INSERT INTO file (requestId,bucket_Name,file_path,filename,urlGenerated) VALUES( %s,%s,%s,%s,%s)"
        val = (requestId, bucket_Name, file_path,destination_file,urlGenerated )
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
        if mycursor:
            mycursor.close()
        if mydb:
            mydb.close()
            
def generateUrlFile(bucket_Name,destination_file):
    try:
        urlGenerated= minio_client.presigned_get_object(bucket_Name, destination_file, expires=timedelta(seconds=3600))
        print(f"URL généré pour le fichier {destination_file} : {urlGenerated}")  
        return urlGenerated      
    except Exception as ex:
        print(f"Erreur inattendue : {ex}")
        return False
    
# Fonction pour consommer le message kafka 
def kafkaService():
    consumer = KafkaConsumer(
        'files_to_convert',
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    print("Worker en attente de messages Kafka...")
    for message in consumer:
        # Télécharger le fichier depuis MinIO
        print(f"Message reçu : {message.value.decode()}")

        pdf_path,bucket_Name,requestId = minioDOwloadFileService(message.value.decode())
       
        

        if pdf_path:
        
            docx_path = pdf_path.replace(".pdf", ".docx")  
            file_path=docx_path
            cv = Converter(pdf_path)
            cv.convert(docx_path,start=0, end=None, 
                       extract_image=True, 
                       detect_orientation=True)
            cv.close()
            print(f"Conversion terminée : {docx_path}")
            destination_file = docx_path.split("/")[-1] 
           
            
            minioUploadDocsFile(bucket_Name,docx_path,destination_file)
            urlGenerated = generateUrlFile(bucket_Name,destination_file)
            sendToBD(requestId,bucket_Name,file_path,destination_file,urlGenerated)
        else:
            print("Le fichier n'a pas pu être téléchargé, conversion annulée.")
            
            

                    


kafkaService()
