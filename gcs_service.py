# /search_instagram/gcs_service.py
import os
from google.cloud import storage
from logging_config import logging
from io import BytesIO
from typing import Optional

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

    def upload_media_from_buffer(self, buffer: BytesIO, destination_blob_name: str) -> Optional[str]:
        """
        Faz o upload de um buffer de mídia em memória para o GCS.

        Args:
            buffer (BytesIO): O buffer em memória contendo os dados da mídia.
            destination_blob_name (str): O nome do blob de destino no GCS.

        Returns:
            str: O caminho GCS completo (gs://...) do arquivo ou None em caso de erro.
        """
        try:
            blob = self.bucket.blob(destination_blob_name)
            # O SDK infere o content_type a partir da extensão do nome do blob
            blob.upload_from_file(buffer, rewind=True)
            gcs_path = f"gs://{self.bucket_name}/{destination_blob_name}"
            logging.info(f"Buffer enviado para {gcs_path} no GCS.")
            return gcs_path
        except Exception as e:
            logging.error(f"Erro ao fazer upload do buffer para o GCS: {e}")
            return None

    def download_media(self, source_blob_name: str, destination_file_name: str) -> bool:
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
