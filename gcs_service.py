# /search_instagram/gcs_service.py
import os
from google.cloud import storage
from logging_config import logging

class GCSService:
    """
    Classe de serviço para interagir com o Google Cloud Storage (GCS).
    """
    def __init__(self):
        """
        Inicializa o cliente do GCS.
        """
        try:
            self.storage_client = storage.Client()
            self.bucket_name = os.getenv("GCS_BUCKET_NAME")
            if not self.bucket_name:
                raise ValueError("Variável de ambiente GCS_BUCKET_NAME não definida.")
            self.bucket = self.storage_client.bucket(self.bucket_name)
            logging.info(f"Conexão com o GCS no bucket '{self.bucket_name}' estabelecida.")
        except Exception as e:
            logging.error(f"Falha ao conectar com o GCS: {e}")
            raise

    def upload_media(self, file_path: str, destination_blob_name: str):
        """
        Faz o upload de um arquivo de mídia para o GCS.

        Args:
            file_path (str): O caminho local do arquivo a ser enviado.
            destination_blob_name (str): O nome do blob de destino no GCS.

        Returns:
            str: A URL pública do arquivo no GCS ou None em caso de erro.
        """
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_path)
            logging.info(f"Arquivo {file_path} enviado para {destination_blob_name} no GCS.")
            return blob.public_url
        except Exception as e:
            logging.error(f"Erro ao fazer upload para o GCS: {e}")
            return None

    def download_media(self, source_blob_name: str, destination_file_name: str):
        """
        Faz o download de um arquivo de mídia do GCS.

        Args:
            source_blob_name (str): O nome do blob de origem no GCS.
            destination_file_name (str): O caminho local para salvar o arquivo.
        
        Returns:
            bool: True se o download for bem-sucedido, False caso contrário.
        """
        try:
            blob = self.bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_name)
            logging.info(f"Arquivo {source_blob_name} baixado para {destination_file_name}.")
            return True
        except Exception as e:
            logging.error(f"Erro ao fazer download do GCS: {e}")
            return False