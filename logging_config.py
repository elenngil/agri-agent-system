import logging
import os
import pathlib
from dotenv import load_dotenv
from tqdm import tqdm
from functools import partialmethod

load_dotenv()

level = logging.DEBUG if os.getenv("ENV") == "dev" else logging.INFO

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

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)