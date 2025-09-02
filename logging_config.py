# /search_instagram/logging_config.py
import logging
import sys

# Configuração básica do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Garante que os logs sejam enviados para a saída padrão
)
