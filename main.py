# /search_instagram/main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from datetime import datetime, timezone
import uuid
from instagram_service import InstagramService
from firestore_service import FirestoreService
from logging_config import logging
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
# Essencial para o desenvolvimento local
load_dotenv()

app = FastAPI(
    title="Search Instagram Service",
    description="Micro-serviço para coleta de dados do Instagram.",
    version="1.0.0"
)

def run_daily_scan_task():
    """
    Função que será executada em background para a coleta diária.
    Orquestra o processo de login, coleta e logging.
    """
    run_id = str(uuid.uuid4())
    firestore_logger = None
    
    try:
        # Inicializa o logger do Firestore para registrar o início
        firestore_logger = FirestoreService()
        firestore_logger.log_system_event(
            run_id=run_id,
            service="Search_Instagram",
            job_type="daily_scan",
            status="started",
            message="Iniciando varredura diária de perfis e hashtags."
        )

        # Inicializa e executa o serviço principal
        service = InstagramService(run_id=run_id)
        service.run_scan()

        # Registra a conclusão
        firestore_logger.log_system_event(
            run_id=run_id,
            service="Search_Instagram",
            job_type="daily_scan",
            status="completed",
            message="Varredura diária concluída com sucesso.",
            end_time=datetime.now(timezone.utc)
            # TODO: Capturar e passar métricas do serviço
        )

    except Exception as e:
        logging.critical(f"[RUN_ID: {run_id}] - Uma exceção não tratada ocorreu na tarefa de background: {e}", exc_info=True)
        if firestore_logger:
            firestore_logger.log_system_event(
                run_id=run_id,
                service="Search_Instagram",
                job_type="daily_scan",
                status="error",
                message="A tarefa de varredura falhou criticamente.",
                error_message=str(e),
                end_time=datetime.now(timezone.utc)
            )
        # Re-raise para que qualquer monitoramento de nível superior possa capturar
        raise

@app.post("/jobs/start-daily-scan", status_code=202, tags=["Jobs"])
async def start_daily_scan(background_tasks: BackgroundTasks):
    """
    Endpoint para iniciar a tarefa de varredura diária de perfis e hashtags.
    Este endpoint é projetado para ser acionado pelo Google Cloud Scheduler.
    """
    logging.info("Recebida requisição para iniciar o job de varredura diária.")
    background_tasks.add_task(run_daily_scan_task)
    return {"message": "Job de varredura diária iniciado em background."}

@app.get("/health", status_code=200, tags=["Monitoring"])
async def health_check():
    """
    Endpoint de health check para o Google Cloud Run.
    Verifica a conectividade com o Firestore.
    """
    try:
        FirestoreService()
        return {"status": "ok", "firestore_connection": "ok"}
    except Exception as e:
        logging.error(f"Health check falhou: {e}")
        raise HTTPException(status_code=503, detail=f"Serviço indisponível. Erro de conexão com o Firestore: {e}")

@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Search Instagram Service está no ar! Acesse /docs para a documentação da API."}

if __name__ == "__main__":
    import uvicorn
    # Para desenvolvimento local, use --reload
    # uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
    uvicorn.run(app, host="0.0.0.0", port=8080)
