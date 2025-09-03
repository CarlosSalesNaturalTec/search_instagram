# /search_instagram/firestore_service.py
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from logging_config import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid

class FirestoreService:
    """
    Classe de serviço para interagir com o Google Firestore, expandida para
    suportar as operações do módulo Search_Instagram.
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

    def get_service_account_for_work(self) -> Optional[Dict[str, Any]]:
        """
        Seleciona a conta de serviço 'active' com o uso mais antigo.

        Returns:
            Um dicionário com os dados da conta ou None se nenhuma estiver disponível.
        """
        try:
            acc_ref = self.db.collection('service_accounts')
            query = acc_ref.where(filter=FieldFilter("status", "==", "active")).order_by("last_used_at", direction=firestore.Query.ASCENDING).limit(1)
            
            accounts = []
            for doc in query.stream():
                account_data = doc.to_dict()
                account_data['doc_id'] = doc.id
                accounts.append(account_data)

            if not accounts:
                logging.warning("Nenhuma conta de serviço ativa encontrada.")
                return None
            
            account = accounts[0]
            logging.info(f"Conta de serviço selecionada para trabalho: {account.get('username')}")
            return account
        except Exception as e:
            logging.error(f"Erro ao buscar conta de serviço no Firestore: {e}")
            return None

    def update_service_account_status(self, username: str, status: str, last_used_at: Optional[datetime] = None) -> bool:
        """
        Atualiza o status e a data de último uso de uma conta de serviço.
        """
        try:
            acc_ref = self.db.collection('service_accounts')
            query = acc_ref.where(filter=FieldFilter("username", "==", username)).limit(1)
            docs = list(query.stream())

            if not docs:
                logging.error(f"Nenhuma conta de serviço encontrada com o username: {username}")
                return False

            doc_id = docs[0].id
            update_data = {"status": status}
            if last_used_at:
                update_data["last_used_at"] = last_used_at
            
            self.db.collection('service_accounts').document(doc_id).update(update_data)
            logging.info(f"Status da conta {username} atualizado para '{status}'.")
            return True
        except Exception as e:
            logging.error(f"Erro ao atualizar status da conta {username}: {e}")
            return False

    def get_active_monitored_profiles(self) -> List[Dict[str, Any]]:
        """
        Busca todos os perfis monitorados que estão ativos.
        """
        return self._get_active_items('monitored_profiles', 'instagram_username')

    def get_active_monitored_hashtags(self) -> List[Dict[str, Any]]:
        """
        Busca todas as hashtags monitoradas que estão ativas.
        """
        return self._get_active_items('monitored_hashtags', 'hashtag_sem_cerquilha')

    def _get_active_items(self, collection_name: str, id_field: str) -> List[Dict[str, Any]]:
        """
        Função auxiliar para buscar itens ativos de uma coleção, garantindo que o
        campo usado como ID do documento esteja presente nos dados retornados.
        """
        try:
            coll_ref = self.db.collection(collection_name)
            query = coll_ref.where(filter=FieldFilter("is_active", "==", True))
            items = []
            for doc in query.stream():
                item_data = doc.to_dict()
                # Garante que o campo que usamos como ID esteja no dicionário
                item_data[id_field] = doc.id
                items.append(item_data)

            logging.info(f"{len(items)} itens ativos encontrados em '{collection_name}'.")
            return items
        except Exception as e:
            logging.error(f"Erro ao buscar itens ativos de '{collection_name}': {e}")
            return []

    def update_monitored_item_scan_time(self, collection_name: str, doc_id: str):
        """
        Atualiza o campo 'last_scanned_at' de um item monitorado.
        """
        try:
            doc_ref = self.db.collection(collection_name).document(doc_id)
            doc_ref.update({"last_scanned_at": datetime.now(timezone.utc)})
            logging.info(f"Timestamp de varredura atualizado para '{doc_id}' em '{collection_name}'.")
        except Exception as e:
            logging.error(f"Erro ao atualizar timestamp de '{doc_id}' em '{collection_name}': {e}")


    def save_instagram_data(self, collection_path: str, data: Dict[str, Any], doc_id: str):
        """
        Salva (cria ou sobrescreve) um documento em uma coleção/sub-coleção.
        """
        try:
            if 'collected_at' not in data:
                data['collected_at'] = datetime.now(timezone.utc)
            
            self.db.collection(collection_path).document(doc_id).set(data, merge=True)
            logging.debug(f"Dados salvos com sucesso em '{collection_path}' com ID '{doc_id}'.")
        except Exception as e:
            logging.error(f"Erro ao salvar dados em '{collection_path}' com ID '{doc_id}': {e}")

    def log_system_event(self, run_id: str, service: str, job_type: str, status: str, message: str, error_message: Optional[str] = None, metrics: Optional[Dict[str, int]] = None, end_time: Optional[datetime] = None):
        """
        Registra um evento no log do sistema.
        """
        try:
            log_ref = self.db.collection('system_logs').document(run_id)
            
            if status == 'started':
                log_entry = {
                    "run_id": run_id,
                    "service": service,
                    "job_type": job_type,
                    "status": status,
                    "message": message,
                    "start_time": datetime.now(timezone.utc),
                    "end_time": None,
                    "error_message": None,
                    "metrics": None
                }
                log_ref.set(log_entry)
                logging.info(f"Log de início de job registrado com run_id: {run_id}")
            else:
                update_data = {
                    "status": status,
                    "message": message,
                    "end_time": end_time or datetime.now(timezone.utc)
                }
                if error_message:
                    update_data['error_message'] = error_message
                if metrics:
                    update_data['metrics'] = metrics
                
                log_ref.update(update_data)
                logging.info(f"Log de finalização de job atualizado para run_id: {run_id}")

        except Exception as e:
            logging.error(f"Erro ao registrar evento de log no Firestore: {e}")
