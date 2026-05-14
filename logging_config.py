"""
logging_config.py
-----------------
Configuración centralizada de logging para todo el sistema.

Debe importarse como PRIMERA línea en main.py y runner.py
para garantizar que las librerías externas no contaminen
el log antes de que se aplique la configuración.

Uso:
    import logging_config  # siempre primera línea
    import logging
    logger = logging.getLogger(__name__)
"""

import logging
import os
import pathlib
from dotenv import load_dotenv
import transformers
from sentence_transformers import SentenceTransformer
import sentence_transformers
from tqdm import tqdm
from functools import partialmethod

load_dotenv()

level = logging.DEBUG if os.getenv("ENV") == "dev" else logging.INFO

# Crear carpeta de logs si no existe
pathlib.Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=level,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/agri_agent.log", encoding="utf-8"),
    ]
)

# Silenciar librerías externas ruidosas
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

transformers.logging.set_verbosity_error()
sentence_transformers.SentenceTransformer.__init_subclass__ = lambda *a, **kw: None
tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)