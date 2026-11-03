import os
from pathlib import Path
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DATA_DIR = ROOT_DIR / "data"
DEFAULT_LOGS_DIR = ROOT_DIR / "logs"


class Settings(BaseModel):
    app_name: str = "CRM GLOBAL CARDS"
    app_version: str = "1.0.0"
    host: str = os.getenv("SATIRO_HOST", "127.0.0.1")
    port: int = int(os.getenv("SATIRO_PORT", "8765"))
    data_dir: Path = Path(os.getenv("SATIRO_DATA_DIR", str(DEFAULT_DATA_DIR)))
    logs_dir: Path = Path(os.getenv("SATIRO_LOGS_DIR", str(DEFAULT_LOGS_DIR)))
    jwt_secret: str = os.getenv(
        "SATIRO_JWT_SECRET",
        "satiro-local-crm-key-change-in-production-9f8e7d6c5b4a3210",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480  # 8h turno comercial
    max_login_attempts: int = 5
    lockout_minutes: int = 15
    bling_api_base_url: str = "https://api.bling.com.br/Api/v3"
    bling_oauth_authorize_url: str = "https://www.bling.com.br/Api/v3/oauth/authorize"
    bling_oauth_token_url: str = "https://www.bling.com.br/Api/v3/oauth/token"
    whatsapp_graph_url: str = "https://graph.facebook.com/v21.0"


settings = Settings()

