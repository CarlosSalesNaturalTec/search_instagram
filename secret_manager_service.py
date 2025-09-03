# /search_instagram/secret_manager_service.py
import os
from google.cloud import secretmanager
from logging_config import logging
from typing import Optional

class SecretManagerService:
    """
    Classe de serviço para interagir com o Google Secret Manager.
    """
    def __init__(self):
        """
        Inicializa o cliente do Secret Manager.
        """
        try:
            self.client = secretmanager.SecretManagerServiceClient()
            self.project_id = os.getenv("GCP_PROJECT_ID")
            if not self.project_id:
                raise ValueError("Variável de ambiente GCP_PROJECT_ID não definida.")
            logging.info("Cliente do Secret Manager inicializado com sucesso.")
        except Exception as e:
            logging.error(f"Falha ao inicializar o cliente do Secret Manager: {e}")
            raise

    def get_secret_payload(self, secret_path: str) -> Optional[bytes]:
        """
        Busca o payload binário de um segredo no Secret Manager.
        Ideal para arquivos de sessão que não devem ser decodificados.

        Args:
            secret_path (str): O caminho completo do recurso do segredo
                               (ex: projects/ID/secrets/NOME/versions/1).

        Returns:
            bytes: O payload do segredo como bytes, ou None em caso de erro.
        """
        try:
            # O nome já é o caminho completo, não precisa montar.
            response = self.client.access_secret_version(request={"name": secret_path})
            payload = response.payload.data
            logging.info(f"Payload do segredo '{secret_path}' acessado com sucesso.")
            return payload
        except Exception as e:
            logging.error(f"Erro ao acessar o payload do segredo '{secret_path}': {e}")
            return None
