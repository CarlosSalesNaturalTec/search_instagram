# Search_Instagram Microservice

Este módulo é responsável pela coleta de dados públicos do Instagram, incluindo posts, comentários e stories.

## Arquitetura

- **API:** FastAPI
- **Coleta:** Instaloader
- **Banco de Dados (Metadados):** Firestore
- **Armazenamento (Mídia):** Google Cloud Storage
- **Gerenciamento de Sessões:** Google Secret Manager

## Endpoints

- `POST /jobs/start-daily-scan`: Inicia uma tarefa em background para a coleta diária de dados de perfis e hashtags monitoradas.
- `GET /health`: Verifica a saúde do serviço.

## Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e preencha as seguintes variáveis:

- `GCP_PROJECT_ID`: ID do seu projeto no Google Cloud.
- `GCS_BUCKET_NAME`: Nome do bucket no GCS onde as mídias serão salvas.
- `FIRESTORE_SERVICE_ACCOUNTS_COLLECTION`: Nome da coleção no Firestore que armazena as contas de serviço do Instagram.

## Relação com Outros Módulos

- **Firestore:**
    - **Lê de:** `service_accounts`, `monitored_profiles`, `monitored_hashtags`.
    - **Escreve em:** `instagram_posts`, `instagram_comments`, `instagram_stories`, `system_logs`.
- **Google Cloud Storage:**
    - **Escreve em:** Salva imagens e vídeos de posts e stories no bucket configurado.
- **Google Secret Manager:**
    - **Lê de:** Acessa os segredos que contêm os arquivos de sessão do Instaloader.
- **api_nlp (Consumidor):**
    - O módulo `api_nlp` consumirá os dados das coleções `instagram_posts` e `instagram_comments` para realizar a análise de sentimento e extração de entidades.
