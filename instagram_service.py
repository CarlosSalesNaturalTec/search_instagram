# /search_instagram/instagram_service.py
import instaloader
from instaloader.exceptions import LoginRequiredException, TooManyRequestsException, ProfileNotExistsException, PrivateProfileNotFollowedException
from logging_config import logging
from firestore_service import FirestoreService
from gcs_service import GCSService
from secret_manager_service import SecretManagerService
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import random
import time
import tempfile
import os
import itertools
import requests
from io import BytesIO

class InstagramService:
    """
    Serviço de orquestração para a coleta de dados do Instagram.
    """
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.firestore_service = FirestoreService()
        self.gcs_service = GCSService()
        self.secret_manager_service = SecretManagerService()
        self.instaloader_instance = None
        self.service_account = None
        self.temp_session_file = None

    def _human_like_pause(self, min_seconds: int = 5, max_seconds: int = 15):
        delay = random.uniform(min_seconds, max_seconds)
        logging.info(f"Pausa estratégica de {delay:.2f} segundos.")
        time.sleep(delay)

    def _setup_instaloader_session(self) -> bool:
        """
        Seleciona uma conta de serviço, baixa a sessão do Secret Manager,
        e inicializa uma instância do Instaloader.
        """
        self.service_account = self.firestore_service.get_service_account_for_work()
        if not self.service_account:
            self.firestore_service.log_system_event(self.run_id, "Search_Instagram", "session_setup", "error", "Nenhuma conta de serviço ativa disponível.")
            return False

        username = self.service_account['username']
        secret_path = self.service_account['secret_manager_path']
        
        try:
            session_content = self.secret_manager_service.get_secret_payload(secret_path)
            if not session_content:
                raise ValueError("Conteúdo da sessão do Secret Manager está vazio.")

            # Usar um arquivo temporário para carregar a sessão
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, prefix=f"{username}_") as tmp_file:
                self.temp_session_file = tmp_file.name
                tmp_file.write(session_content)

            self.instaloader_instance = instaloader.Instaloader()
            self.instaloader_instance.load_session_from_file(username, self.temp_session_file)
            logging.info(f"Sessão do Instaloader para '{username}' carregada com sucesso a partir de arquivo temporário.")
            
            # Testar o login para validar a sessão imediatamente
            self.instaloader_instance.test_login()
            logging.info(f"Login para '{username}' testado e validado com sucesso.")
            return True

        except LoginRequiredException as e:
            logging.error(f"Sessão para a conta '{username}' é inválida ou expirou. Marcando para renovação. Erro: {e}")
            self.firestore_service.update_service_account_status(username, 'session_expired')
            self.firestore_service.log_system_event(self.run_id, "Search_Instagram", "session_validation", "error", f"Sessão para {username} é inválida.", str(e))
            return False
        except Exception as e:
            logging.error(f"Falha inesperada ao configurar a sessão do Instaloader para '{username}': {e}")
            self.firestore_service.log_system_event(self.run_id, "Search_Instagram", "session_setup", "error", f"Erro ao configurar sessão para {username}.", str(e))
            return False

    def _cleanup_temp_session_file(self):
        if self.temp_session_file and os.path.exists(self.temp_session_file):
            os.remove(self.temp_session_file)
            logging.info(f"Arquivo de sessão temporário '{self.temp_session_file}' removido.")
            self.temp_session_file = None

    def _download_and_upload_media(self, media_url: str, gcs_path: str) -> Optional[str]:
        """
        Baixa uma mídia da URL para a memória e faz o upload para o GCS.
        """
        try:
            response = requests.get(media_url, stream=True, timeout=60)
            response.raise_for_status()
            media_buffer = BytesIO(response.content)
            
            gcs_full_path = self.gcs_service.upload_media_from_buffer(media_buffer, gcs_path)
            if gcs_full_path:
                logging.info(f"Mídia enviada com sucesso para: {gcs_full_path}")
            return gcs_full_path
        except requests.RequestException as e:
            logging.error(f"Erro ao baixar mídia da URL {media_url}: {e}")
        except Exception as e:
            logging.error(f"Erro ao fazer upload da mídia para {gcs_path}: {e}")
        return None

    def _process_post(self, post: instaloader.Post):
        """
        Processa um único post, salva seus metadados, mídia e comentários.
        """
        post_date_str = post.date_utc.strftime('%Y-%m')
        file_extension = '.mp4' if post.is_video else '.jpg'
        gcs_path = f"instagram/posts/{post.owner_username}/{post_date_str}/{post.shortcode}{file_extension}"

        media_url = post.video_url if post.is_video else post.url
        gcs_media_path = self._download_and_upload_media(media_url, gcs_path)

        post_data = {
            "owner_username": post.owner_username,
            "caption": post.caption,
            "post_date_utc": post.date_utc,
            "likes_count": post.likes,
            "comments_count": post.comments,
            "media_type": post.typename,
            "gcs_media_path": gcs_media_path,
            "nlp_status": "pending" # Adiciona status para o job de NLP
        }
        self.firestore_service.save_instagram_data('instagram_posts', post_data, post.shortcode)
        
        # Processar comentários
        comments_iterator = post.get_comments()
        for comment in itertools.islice(comments_iterator, 100):
            comment_data = {
                "post_shortcode": post.shortcode,
                "text": comment.text,
                "username": comment.owner.username,
                "likes_count": comment.likes_count,
                "comment_date_utc": comment.created_at_utc,
                "nlp_status": "pending" # Adiciona status para o job de NLP
            }
            # Salva como sub-coleção do post
            self.firestore_service.save_instagram_data(f'instagram_posts/{post.shortcode}/instagram_comments', comment_data, str(comment.id))
        
        self._human_like_pause(8, 22)

    def _process_story(self, story: instaloader.StoryItem, owner_username: str):
        """
        Processa um único story, salva seus metadados e mídia.
        """
        story_date_str = story.date_utc.strftime('%Y-%m')
        file_extension = '.mp4' if story.is_video else '.jpg'
        gcs_path = f"instagram/stories/{owner_username}/{story_date_str}/{story.mediaid}{file_extension}"

        media_url = story.video_url if story.is_video else story.url
        gcs_media_path = self._download_and_upload_media(media_url, gcs_path)

        story_data = {
            "owner_username": owner_username,
            "story_date_utc": story.date_utc,
            "expires_at_utc": story.date_utc + timedelta(hours=24),
            "media_type": "video" if story.is_video else "image",
            "gcs_media_path": gcs_media_path,
        }
        self.firestore_service.save_instagram_data('instagram_stories', story_data, str(story.mediaid))
        self._human_like_pause(3, 8) # Pausa menor para stories

    def run_scan(self):
        """
        Ponto de entrada principal para executar a varredura de perfis e hashtags.
        """
        if not self._setup_instaloader_session():
            return

        try:
            # Lógica de varredura de perfis
            profiles_to_scan = self.firestore_service.get_active_monitored_profiles()
            for profile_info in profiles_to_scan:
                username = profile_info.get('instagram_username')
                if not username: continue
                
                logging.info(f"Iniciando varredura do perfil: {username}")
                try:
                    profile = instaloader.Profile.from_username(self.instaloader_instance.context, username)
                    
                    # 1. Coletar Posts
                    logging.info(f"Coletando posts para o perfil: {username}")
                    for post in profile.get_posts():
                        self._process_post(post)
                    
                    # 2. Coletar Stories
                    logging.info(f"Coletando stories para o perfil: {username}")
                    for story in self.instaloader_instance.get_stories(userids=[profile.userid]):
                        for item in story.get_items():
                            self._process_story(item, profile.username)

                    # Atualizar last_scanned_at para o perfil
                    self.firestore_service.update_monitored_item_scan_time('monitored_profiles', username)
                    self._human_like_pause(180, 300) # Pausa longa entre perfis

                except ProfileNotExistsException:
                    logging.warning(f"Perfil '{username}' não encontrado. Considerar desativar.")
                except PrivateProfileNotFollowedException:
                    logging.warning(f"Perfil '{username}' é privado e não é seguido pela conta de serviço. Pulando.")
                except Exception as e:
                    logging.error(f"Erro ao processar o perfil '{username}': {e}", exc_info=True)

            # TODO: Adicionar lógica de varredura de hashtags aqui

        except TooManyRequestsException as e:
            logging.warning(f"Recebida exceção TooManyRequestsException. Encerrando o job e entrando em backoff. Erro: {e}")
            self.firestore_service.log_system_event(self.run_id, "Search_Instagram", "data_collection", "warning", "TooManyRequestsException recebida.", str(e))
            time.sleep(random.uniform(900, 1800)) # Backoff
        except Exception as e:
            logging.critical(f"Erro não tratado durante a execução da varredura: {e}", exc_info=True)
            self.firestore_service.log_system_event(self.run_id, "Search_Instagram", "data_collection", "error", "Erro crítico na varredura.", str(e))
        finally:
            # Atualizar o last_used_at da conta de serviço
            if self.service_account:
                self.firestore_service.update_service_account_status(
                    self.service_account['username'], 
                    'active', 
                    last_used_at=datetime.now(timezone.utc)
                )
            self._cleanup_temp_session_file()