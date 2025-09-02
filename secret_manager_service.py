# /search_instagram/secret_manager_service.py
import os
from google.cloud import secretmanager
from logging_config import logging

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

    def get_secret(self, secret_id: str, version_id: str = "latest"):
        """
        Busca o valor de um segredo no Secret Manager.

        Args:
            secret_id (str): O ID do segredo.
            version_id (str): A versão do segredo (padrão: "latest").

        Returns:
            str: O valor do segredo ou None em caso de erro.
        """
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
            response = self.client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")
            logging.info(f"Segredo '{secret_id}' acessado com sucesso.")
            return payload
        except Exception as e:
            logging.error(f"Erro ao acessar o segredo '{secret_id}': {e}")
            return None