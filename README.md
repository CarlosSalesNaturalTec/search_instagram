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

## 8. Como funciona

Ao executar o endpoint /jobs/start-daily-scan, acontece o seguinte fluxo assíncrono:

O endpoint não executa a varredura diretamente. Em vez disso, ele age como um gatilho que agenda uma tarefa para ser executada em segundo plano (background task), garantindo que a requisição HTTP receba uma resposta imediata e o processo de coleta, que pode ser longo, rode de forma independente.

Aqui está o passo a passo detalhado do que ocorre:

1. Requisição e Resposta Imediata:
    * Uma requisição POST é enviada para /jobs/start-daily-scan.
    * O servidor FastAPI recebe a requisição na função start_daily_scan.
    * Imediatamente, ele utiliza o background_tasks.add_task() para agendar a execução da função run_daily_scan_task.
    * O servidor responde com um status 202 Accepted e a mensagem {"message": "Job de varredura diária iniciado em background."}. A conexão com o
        cliente (ex: Google Cloud Scheduler) é encerrada aqui.

2. Início da Tarefa em Background (`run_daily_scan_task`):
    * A função run_daily_scan_task começa a ser executada de forma independente.
    * Um ID de execução único (run_id) é gerado usando uuid.uuid4() para rastrear toda a operação.
    * O serviço de Firestore é inicializado e um log é imediatamente gravado na coleção system_logs com o status "started", informando que a varredura
        diária foi iniciada.

3. Execução do Serviço Principal (`InstagramService.run_scan`):
    * A lógica principal é encapsulada dentro da classe InstagramService. A função run_scan() é chamada, e é aqui que a coleta de dados acontece. Com base na documentação, este processo envolve:
        * Seleção e Login da Conta: O serviço consulta a coleção service_accounts no Firestore, seleciona uma conta com status "active" (a usada menos recentemente) e busca seu arquivo de sessão no Google Secret Manager para se autenticar no Instagram via Instaloader.
        * Busca dos Alvos: O serviço lê as coleções monitored_profiles e monitored_hashtags para saber quais perfis e hashtags devem ser escaneados.
        * Coleta de Dados: Para cada alvo, o Instaloader é usado para buscar novos posts, stories e comentários, extraindo os metadados especificados na documentação (como shortcode, caption, likes_count, etc.).
        * Persistência de Mídia no GCS: Para cada post ou story com imagem ou vídeo, a mídia é baixada para a memória e enviada para o Google Cloud Storage (GCS). O caminho do arquivo no GCS (ex: gs://bucket/instagram/posts/...) é salvo no campo gcs_media_path do documento no Firestore.
        * Persistência de Metadados no Firestore: Os metadados de posts, stories e comentários são salvos nas respectivas coleções (instagram_posts, instagram_stories, instagram_comments).
        * Estratégias Anti-Bloqueio: Durante todo o processo, o serviço aplica pausas aleatórias de "cadência humana" entre as requisições para evitar ser bloqueado pelo Instagram.

4. Tratamento de Erros:
    * Todo o processo dentro de run_daily_scan_task está envolto em um bloco try...except.
    * Se ocorrer qualquer erro inesperado (ex: falha de rede, erro de parsing), a exceção é capturada.
    * Um log de erro é gravado na coleção system_logs com o status "error", contendo a mensagem de erro detalhada. O erro também é logado no console do Cloud Run.
    * A documentação detalha tratamentos específicos: se a sessão expirar (LoginRequiredException), o status da conta em service_accounts é atualizado para "session_expired". Se houver um bloqueio temporário (TooManyRequestsException), o serviço entra em um longo período de espera (backoff).

5. Conclusão e Log Final:
    * Se a varredura for concluída sem erros fatais, a função run_daily_scan_task grava um último log na coleção system_logs com o status "completed", informando que a tarefa terminou com sucesso e registrando o end_time.

Em resumo, o endpoint atua como um gatilho assíncrono para um processo de coleta robusto e resiliente, que gerencia autenticação segura, busca alvos dinamicamente, persiste dados em dois serviços diferentes (Firestore e GCS) e possui um sistema detalhado de logging e tratamento de erros.

**Carga histórica X carga diária**

1. Na Primeira Execução (Carga Histórica)

  Quando um perfil é adicionado e o serviço é executado pela primeira vez para aquele alvo, a aplicação vai tentar buscar TODAS as publicações do perfil, desde a mais recente até a mais antiga.

  O trecho de código responsável por isso é:

   1 # Linha 191
   2 logging.info(f"Coletando posts para o perfil: {username}")
   3 for post in profile.get_posts():
   4     self._process_post(post)

  A função profile.get_posts() da biblioteca instaloader é um gerador (iterator) que, por padrão, percorre todo o histórico de posts de um perfil. Não há nenhum filtro de data sendo aplicado no código. Portanto, a primeira varredura é uma "carga histórica" completa, o que pode ser um processo longo e intensivo para perfis com milhares de publicações.

  2. Nas Execuções Seguintes (Carga Incremental)

  A partir do segundo dia, o comportamento muda drasticamente. A aplicação vai baixar apenas as publicações NOVAS, ou seja, aquelas que foram feitas desde a última varredura.

  Isso acontece porque a biblioteca instaloader é projetada para ser "stateful". Ela utiliza o arquivo de sessão não apenas para autenticação, mas também para registrar o progresso das coletas.

  Como funciona:

   1. Carregamento da Sessão: No início de cada execução, a função _setup_instaloader_session carrega o arquivo de sessão (self.instaloader_instance.load_session_from_file(...)).
   2. Execução do Loop: Quando o mesmo loop for post in profile.get_posts(): é executado novamente no dia seguinte, o instaloader começa a buscar os posts do mais recente para o mais antigo.
   3. Ponto de Parada: Assim que o instaloader encontra um post que ele já processou e salvou na execução anterior (cuja informação está no arquivo de sessão), ele para a iteração para aquele perfil.
   4. Resultado: Apenas os posts que ele ainda não "conhecia" (os novos) são processados e salvos.

  Este mecanismo torna as execuções subsequentes muito mais rápidas e eficientes, focando apenas no conteúdo novo e evitando reprocessar dados desnecessariamente.

  E os Stories?

  Para os Stories, o comportamento é sempre o mesmo:

   1 # Linha 195
   2 for story in self.instaloader_instance.get_stories(userids=[profile.userid]):
   3     for item in story.get_items():
   4         self._process_story(item, profile.username)

  A função get_stories busca apenas os stories que estão atualmente ativos (publicados nas últimas 24 horas). Portanto, a cada execução, o serviço vai coletar os stories que estiverem no ar naquele momento, independentemente do que foi coletado no dia anterior.

  Com base na documentação de contexto (contextDoc_instagram.md), o cadastro do username do parlamentar e dos concorrentes é realizado através do
  Frontend da plataforma, em uma área específica de Gerenciamento de Alvos.

  O processo funciona da seguinte maneira:

   1. Interface no Frontend: Existe uma interface de usuário (provavelmente uma página de administração) que oferece um "CRUD completo" (Criar, Ler, Atualizar, Deletar) para a coleção monitored_profiles.

   2. Formulário de Cadastro: Nessa interface, um usuário com as devidas permissões preenche um formulário para adicionar um novo perfil a ser monitorado.
      Os campos essenciais nesse formulário seriam:
       * Username do Instagram: O nome do perfil a ser monitorado (ex: jairbolsonaro, lulaoficial).
       * Tipo de Perfil: Um campo de seleção ou dropdown onde o usuário classifica o perfil. É aqui que a distinção é feita. As opções são:
           * parlamentar (para o perfil do próprio político)
           * concorrente (para adversários políticos)
           * midia (para veículos de imprensa, influenciadores, etc.)
       * Status: Um campo para ativar ou desativar o monitoramento (is_active).

   3. Armazenamento no Firestore: Quando o formulário é salvo, o frontend envia os dados para o backend, que os armazena como um novo documento na coleção monitored_profiles do Firestore. O ID do documento é o próprio instagram_username.

  Exemplo de como os dados ficariam no Firestore:

   * Documento 1:
       * ID: nome_do_parlamentar
       * type: "parlamentar"
       * is_active: true

   * Documento 2:
       * ID: nome_do_concorrente_1
       * type: "concorrente"
       * is_active: true

   * Documento 3:
       * ID: portal_de_noticias_local
       * type: "midia"
       * is_active: true

  O micro-serviço search_instagram, ao ser executado, simplesmente lê todos os documentos da coleção monitored_profiles onde is_active seja true e inicia a varredura, sem precisar saber a priori qual é o "principal" e quais são os "concorrentes". Essa lógica de diferenciação é aplicada posteriormente, na camada de visualização (Frontend/Dashboards), que utiliza o campo type para filtrar e comparar os dados corretamente.