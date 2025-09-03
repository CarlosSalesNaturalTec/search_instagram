# Search_Instagram Microservice

Este módulo é responsável pela coleta de dados públicos do Instagram, incluindo posts, comentários e stories.

## Arquitetura

- **API:** FastAPI
- **Coleta:** Instaloader
- **Banco de Dados (Metadados):** Firestore
- **Armazenamento (Mídia):** Google Cloud Storage
- **Gerenciamento de Sessões:** Google Secret Manager

---

## Configuração do Ambiente Local

Para executar este serviço em seu ambiente de desenvolvimento, siga estes passos:

1.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure as Credenciais do Google Cloud:**
    *   Faça o download do arquivo JSON da sua **Conta de Serviço** do Google Cloud. Esta conta deve ter permissão para acessar Firestore, Cloud Storage e Secret Manager.
    *   Salve este arquivo JSON em um local seguro, por exemplo, dentro da pasta `/config` deste módulo.

3.  **Crie o arquivo de ambiente:**
    *   Copie o arquivo `.env.example` e renomeie a cópia para `.env`.
    *   Abra o arquivo `.env` e preencha as variáveis:

    ```dotenv
    # ID do seu projeto no Google Cloud
    GCP_PROJECT_ID="seu-projeto-gcp"

    # Nome do bucket no GCS onde as mídias serão salvas
    GCS_BUCKET_NAME="seu-bucket-de-midia"

    # (MUITO IMPORTANTE) Caminho para o arquivo de credenciais
    # Use o caminho absoluto para o arquivo JSON que você baixou.
    # Exemplo Windows: GOOGLE_APPLICATION_CREDENTIALS="C:\Users\SeuUser\projeto\config\credenciais.json"
    # Exemplo Linux/Mac: GOOGLE_APPLICATION_CREDENTIALS="/home/user/projeto/config/credenciais.json"
    GOOGLE_APPLICATION_CREDENTIALS="caminho/absoluto/para/seu/arquivo.json"
    ```

4.  **Execute a Aplicação:**
    ```bash
    uvicorn main:app --reload --port 8080
    ```
    A aplicação agora estará rodando em `http://localhost:8080` e autenticada corretamente com os serviços do Google Cloud.

---

## Endpoints

- `POST /jobs/start-daily-scan`: Inicia uma tarefa em background para a coleta diária de dados de perfis e hashtags monitoradas.
- `GET /health`: Verifica a saúde do serviço e a conexão com o Firestore.

---

## Relação com Outros Módulos

- **Firestore:**
    - **Lê de:** `service_accounts`, `monitored_profiles`, `monitored_hashtags`.
    - **Escreve em:** `instagram_posts`, `instagram_comments` (sub-coleção), `instagram_stories`, `system_logs`.
- **Google Cloud Storage:**
    - **Escreve em:** Salva imagens e vídeos de posts e stories no bucket configurado.
- **Google Secret Manager:**
    - **Lê de:** Acessa os segredos que contêm os arquivos de sessão do Instaloader.
- **api_nlp (Consumidor):**
    - O módulo `api_nlp` consumirá os dados das coleções `instagram_posts` e `instagram_comments` para realizar a análise de sentimento e extração de entidades.