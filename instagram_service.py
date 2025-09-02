# /search_instagram/instagram_service.py
from logging_config import logging
from firestore_service import FirestoreService
from gcs_service import GCSService
from secret_manager_service import SecretManagerService
# Supondo que teremos uma biblioteca/módulo para interagir com a API do Instagram
# from instagram_api_client import InstagramAPIClient 

class InstagramService:
    """
    Serviço de orquestração para a coleta de dados do Instagram.
    """
    def __init__(self):
        """
        Inicializa todos os serviços necessários.
        """
        try:
            self.firestore_service = FirestoreService()
            self.gcs_service = GCSService()
            self.secret_manager_service = SecretManagerService()
            
            # Exemplo de como obter a chave da API do Secret Manager
            # api_key = self.secret_manager_service.get_secret("INSTAGRAM_API_KEY")
            # self.instagram_client = InstagramAPIClient(api_key=api_key)
            
            logging.info("InstagramService inicializado com todas as dependências.")
        except Exception as e:
            logging.error(f"Falha ao inicializar o InstagramService: {e}")
            raise

    def search_and_save_posts(self, search_term: str):
        """
        Busca posts no Instagram com base em um termo e os salva no nosso sistema.

        Args:
            search_term (str): O termo a ser buscado.
        """
        logging.info(f"Iniciando busca por posts com o termo: '{search_term}'")
        
        try:
            # 1. Buscar posts usando o cliente da API do Instagram (lógica a ser implementada)
            # posts = self.instagram_client.search_posts(term=search_term, count=50)
            posts = [] # Placeholder
            logging.info(f"{len(posts)} posts encontrados para o termo '{search_term}'.")

            if not posts:
                logging.warning("Nenhum post encontrado.")
                return

            for post in posts:
                # 2. Para cada post, fazer o download da mídia (se houver)
                media_url = None
                if post.get("media_url"):
                    # Lógica para baixar o arquivo temporariamente
                    local_media_path = f"/tmp/{post['id']}.jpg" 
                    # download_media(post.get("media_url"), local_media_path)

                    # 3. Fazer upload da mídia para o GCS
                    blob_name = f"instagram_media/{post['id']}.jpg"
                    # media_url = self.gcs_service.upload_media(local_media_path, blob_name)
                
                # 4. Preparar os dados para salvar no Firestore
                post_data = {
                    "id": post.get("id"),
                    "user": post.get("user"),
                    "caption": post.get("caption"),
                    "likes": post.get("likes"),
                    "comments_count": post.get("comments_count"),
                    "timestamp": post.get("timestamp"),
                    "gcs_media_url": media_url,
                    "search_term": search_term
                }

                # 5. Salvar os dados do post no Firestore
                self.firestore_service.save_instagram_post(post_data)

            logging.info("Processo de busca e salvamento de posts concluído com sucesso.")

        except Exception as e:
            logging.error(f"Erro durante o processo de busca e salvamento de posts: {e}")

# Exemplo de uso (para fins de teste)
if __name__ == '__main__':
    # Para testar, você precisaria ter as variáveis de ambiente configuradas
    # e as credenciais do GCP disponíveis no ambiente.
    try:
        service = InstagramService()
        # service.search_and_save_posts("exemplo_termo")
        logging.info("Teste de inicialização do InstagramService bem-sucedido.")
    except Exception as e:
        logging.error(f"Falha no teste de inicialização: {e}")