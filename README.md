# Módulo de Coleta do Instagram (search_instagram)

## 1. Visão Geral e Arquitetura

O **Search_Instagram** é um micro-serviço de inteligência e escuta ativa, projetado para ser desacoplado e autônomo. Sua responsabilidade principal é a coleta, enriquecimento primário e armazenamento de dados públicos do Instagram. Ele opera através de jobs agendados e expõe os dados processados para o restante da plataforma através de coleções no Firestore.

### 1.1. Pilha Tecnológica

*   **Linguagem:** Python 3.9+
*   **Framework API:** FastAPI (para criação de endpoints e gerenciamento de Background Tasks)
*   **Biblioteca de Coleta:** Instaloader
*   **Hospedagem:** Google Cloud Run (conteinerizado com Docker)
*   **Banco de Dados (Metadados):** Google Firestore
*   **Armazenamento de Mídia (Data Lake):** Google Cloud Storage (GCS)
*   **Agendamento:** Google Cloud Scheduler
*   **Gerenciamento de Segredos:** Google Secret Manager

## 2. Relação com Outros Módulos

Este módulo é a fundação da análise de Instagram e interage com outros componentes da plataforma da seguinte forma:

*   **Frontend:** O frontend fornece a interface para o usuário cadastrar as **Contas de Serviço** (que serão usadas para a coleta), os **Perfis Alvo** e as **Hashtags Alvo**. Ele também consome os dados coletados para exibir os dashboards.
*   **API_NLP:** Este módulo consome os dados textuais brutos (legendas e comentários) coletados pelo `search_instagram` e salvos nas coleções `instagram_posts` e `instagram_comments`. Ele enriquece esses documentos com análise de sentimento, extração de entidades e moderação de conteúdo.
*   **Google Cloud Storage:** Todas as mídias (imagens e vídeos de posts e stories) são armazenadas no GCS. O `search_instagram` salva o caminho do arquivo (`gcs_media_path`) no respectivo documento do Firestore.

## 3. Modelo de Dados (Coleções do Firestore)

| Coleção | Propósito e Campos Notáveis |
| :--- | :--- |
| **`service_accounts`** | Gerencia o pool de contas do Instagram usadas para a coleta. **Campos:** `username`, `secret_manager_path`, `status` ('active', 'session_expired', 'banned'). |
| **`monitored_profiles`** | Cadastro dos perfis-alvo a serem monitorados. **Campos:** `instagram_username`, `type` ('parlamentar', 'concorrente', 'midia'), `is_active`. |
| **`monitored_hashtags`** | Cadastro das hashtags-alvo a serem monitoradas. **Campos:** `hashtag_sem_cerquilha`, `is_active`. |
| **`instagram_posts`** | Armazena metadados de cada post coletado. **Campos:** `owner_username`, `caption`, `post_date_utc`, `likes_count`, `comments_count`, `gcs_media_path`. |
| **`instagram_comments`** | Sub-coleção de `instagram_posts`, armazena os comentários de cada post. **Campos:** `text`, `username`, `likes_count`. |
| **`instagram_stories`** | Armazena metadados de cada Story. **Campos:** `owner_username`, `story_date_utc`, `gcs_media_path`. |
| **`system_logs`** | Coleção centralizada para logs de auditoria e depuração de todos os micro-serviços. |

## 4. Pré-requisitos e Cadastros Necessários (Setup)

Para que o módulo funcione corretamente, os seguintes cadastros devem ser realizados através do frontend da plataforma:

### 4.1. Contas de Serviço (`service_accounts`)

O sistema precisa de pelo menos uma conta do Instagram válida para realizar a coleta de dados.

**Exemplo de Cadastro:**

1.  **Gere o Arquivo de Sessão:** Em sua máquina local com o Instaloader instalado, execute o comando:
    ```bash
    instaloader --login=sua_conta_de_coleta
    ```
    Isso criará um arquivo chamado `sua_conta_de_coleta` no diretório.
2.  **Cadastre no Frontend:**
    *   Acesse a área de "Gerenciamento de Contas de Serviço".
    *   Clique em "Adicionar Conta".
    *   **Username:** `sua_conta_de_coleta`
    *   **Arquivo de Sessão:** Faça o upload do arquivo gerado no passo 1.
    *   O sistema irá salvar a sessão de forma segura no Google Secret Manager e definir o status da conta como `active`.

### 4.2. Perfis Monitorados (`monitored_profiles`)

Cadastre os perfis do Instagram que você deseja monitorar.

**Exemplo de Cadastro:**

*   **Username:** `jairmessiasbolsonaro`
*   **Tipo:** `Parlamentar` (ou `Concorrente`, `Mídia`)
*   **Status:** `Ativo`

### 4.3. Hashtags Monitoradas (`monitored_hashtags`)

Cadastre as hashtags que você deseja acompanhar.

**Exemplo de Cadastro:**

*   **Hashtag:** `segurancapublica` (sem a cerquilha `#`)
*   **Status:** `Ativo`

## 5. Passo a Passo de Uso (Fluxo de Operação)

1.  **Configuração Inicial:** Realize os cadastros descritos na seção 4.
2.  **Execução do Job:** O job de coleta é acionado automaticamente via Google Cloud Scheduler (diariamente às 23:30hs).
3.  **Processo de Coleta:**
    *   O `search_instagram` seleciona uma `service_account` ativa.
    *   Ele percorre a lista de `monitored_profiles` e `monitored_hashtags` ativos.
    *   Coleta novos posts, comentários e stories desde a última verificação.
    *   Salva os metadados no Firestore e as mídias no Google Cloud Storage.
4.  **Processamento NLP:** O módulo `api_nlp` é acionado em seguida (às 00:00hs) para analisar os textos coletados.
5.  **Visualização:** Acesse o Dashboard do Instagram no frontend para visualizar os dados e análises.

## 6. Como Implantar (Deploy no Google Cloud Run)

O deploy é feito via container Docker.

1.  **Construir a Imagem:**
    ```bash
    gcloud builds submit --tag gcr.io/[PROJECT_ID]/search-instagram ./search_instagram
    ```
2.  **Implantar o Serviço:**
    ```bash
    gcloud run deploy search-instagram \
      --image gcr.io/[PROJECT_ID]/search-instagram \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated \
      --port 8000 \
      --memory 512Mi \
      --cpu 1 \
      --concurrency 1 \
      --timeout 600s \
      --min-instances 0 \
      --max-instances 3
    ```
3.  **Agendar o Job (Cloud Scheduler):**
    *   Crie um novo job no Google Cloud Scheduler.
    *   **Frequência:** `30 23 * * *` (às 23:30hs, todos os dias).
    *   **Alvo:** `HTTP`.
    *   **URL:** A URL do serviço `search-instagram` implantado, seguida pelo endpoint do job (ex: `https://search-instagram-xyz-uc.a.run.app/jobs/start-daily-scan`).
    *   **Método HTTP:** `POST`.

## 7. Dashboard de Análise (Frontend)

O frontend apresenta os dados coletados em um dashboard com 4 abas principais, que são alimentadas pelos dados enriquecidos pelo `api_nlp`.

| Aba | Objetivo Estratégico | Gráficos / Artefatos Chave |
| :--- | :--- | :--- |
| **1. Pulso do Dia** | Resumo diário do ecossistema digital. | **Cards de KPIs**, **Carrossel de Stories Recentes**, **Balanço de Sentimento do Dia**, **Nuvem de Palavras** com os principais termos. |
| **2. Análise de Desempenho** | Entender a performance da própria comunicação. | **Evolução do Engajamento** (gráfico de linhas), **Performance por Tipo de Conteúdo** (gráfico de barras), **Ranking de Posts**, **Top 5 Apoiadores/Críticos**. |
| **3. Inteligência Competitiva** | Benchmarking contra adversários políticos. | **Head-to-Head de Engajamento** (gráfico de linhas), **Comparativo de Estratégia de Conteúdo**, **Nuvem de Palavras Comparativa**. |
| **4. Radar de Pautas** | Entender o que a sociedade e a mídia estão falando. | **Feed da Hashtag** (visual), **Sentimento da Pauta ao Longo do Tempo** (gráfico de linhas), **Principais Influenciadores da Pauta**. |