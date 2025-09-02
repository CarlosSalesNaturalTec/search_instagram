# Arquivo principal da API FastAPI
from fastapi import FastAPI, BackgroundTasks
from datetime import datetime
import uuid

app = FastAPI()

# Exemplo de como registrar um log de sistema (será movido para um serviço dedicado)
def log_system_event(run_id: str, job_type: str, status: str, message: str, service: str = "Search_Instagram", metrics: dict = None):
    """
    Função temporária para simular o registro de logs.
    Em uma implementação real, isso escreveria no Firestore.
    """
    print(f"[{datetime.utcnow().isoformat()}] - RUN_ID: {run_id}")
    print(f"  Service: {service}")
    print(f"  JobType: {job_type}")
    print(f"  Status: {status}")
    print(f"  Message: {message}")
    if metrics:
        print(f"  Metrics: {metrics}")

def run_daily_scan_task():
    """
    Função que será executada em background para a coleta diária.
    """
    run_id = str(uuid.uuid4())
    log_system_event(run_id, "daily_profile_scan", "started", "Iniciando varredura diária de perfis e hashtags.")
    
    # Aqui entrará a lógica principal de coleta:
    # 1. Selecionar conta de serviço
    # 2. Carregar sessão
    # 3. Buscar perfis/hashtags monitoradas
    # 4. Iniciar coleta
    # 5. Tratar exceções
    
    # Simulação de conclusão
    log_system_event(run_id, "daily_profile_scan", "completed", "Varredura diária concluída com sucesso.", metrics={"processed": 0, "new_posts": 0})


@app.post("/jobs/start-daily-scan", status_code=202)
async def start_daily_scan(background_tasks: BackgroundTasks):
    """
    Endpoint para iniciar a tarefa de varredura diária de perfis e hashtags.
    Utiliza BackgroundTasks para retornar uma resposta imediata.
    """
    background_tasks.add_task(run_daily_scan_task)
    return {"message": "Job de varredura diária iniciado em background."}

@app.get("/health", status_code=200)
async def health_check():
    """
    Endpoint de health check para o Cloud Run.
    """
    return {"status": "ok"}
