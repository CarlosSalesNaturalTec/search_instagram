# /search_instagram/firestore_service.py
import os
from google.cloud import firestore
from logging_config import logging

class FirestoreService:
    """
    Classe de serviço para interagir com o Google Firestore.
    """
    def __init__(self):
        """
        Inicializa o cliente do Firestore.
        """
        try:
            self.db = firestore.Client()
            logging.info("Conexão com o Firestore estabelecida com sucesso.")
        except Exception as e:
            logging.error(f"Falha ao conectar com o Firestore: {e}")
            raise

    def save_instagram_post(self, post_data: dict):
        """
        Salva os dados de um post do Instagram no Firestore.

        Args:
            post_data (dict): Dicionário contendo os dados do post.
        
        Returns:
            str: O ID do documento criado no Firestore.
        """
        try:
            collection_name = os.getenv("FIRESTORE_COLLECTION", "instagram_posts")
            doc_ref = self.db.collection(collection_name).add(post_data)
            logging.info(f"Post salvo com sucesso no Firestore com o ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logging.error(f"Erro ao salvar post no Firestore: {e}")
            return None

    def get_document_by_id(self, doc_id: str):
        """
        Busca um documento no Firestore pelo seu ID.

        Args:
            doc_id (str): O ID do documento a ser buscado.

        Returns:
            dict: Os dados do documento encontrado ou None se não existir.
        """
        try:
            collection_name = os.getenv("FIRESTORE_COLLECTION", "instagram_posts")
            doc_ref = self.db.collection(collection_name).document(doc_id)
            document = doc_ref.get()
            if document.exists:
                logging.info(f"Documento com ID {doc_id} encontrado.")
                return document.to_dict()
            else:
                logging.warning(f"Documento com ID {doc_id} não encontrado.")
                return None
        except Exception as e:
            logging.error(f"Erro ao buscar documento no Firestore: {e}")
            return None