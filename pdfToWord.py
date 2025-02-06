import PyPDF2  
import json
import os
from pdf2docx import Converter


def lambda_handler(event, context):
    if 'body' in event and event['body']:
        body = json.loads(event['body'])
        if 'file' in body and body['file']:
            file_data = body['file'].encode('utf-8')
            file_name = body['file_name'] if 'file_name' in body else 'uploaded_file'
            
            # Sauvegarder le fichier PDF dans /tmp avec un nom de fichier unique
            file_path_pdf = os.path.join('/tmp', file_name+'.pdf')
            with open(file_path_pdf, 'wb') as f:
                f.write(file_data)
            
            # Convertir le fichier PDF en DOCX
            cv = Converter(file_path_pdf)
            file_path_docx = os.path.join('/tmp', file_name+'.docx') 
            cv.convert(file_path_docx)
            cv.close()
            
            # Retourner le chemin du fichier DOCX
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Fichier converti avec succès', 'file_path': file_path_docx})
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Le champ "file" est manquant dans la requête'})
            }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Aucun corps de requête trouvé'})
        }
