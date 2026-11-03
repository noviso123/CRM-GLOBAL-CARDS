from datetime import date, datetime
from typing import Optional


def now_iso() -> str:
    """Retorna data/hora atual no padrão ISO de 19 caracteres (YYYY-MM-DDTHH:MM:SS)."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def today_dbf() -> str:
    """Retorna a data atual no formato dBase D(8) YYYYMMDD."""
    return date.today().strftime("%Y%m%d")


def format_date_dbf(value: Optional[str]) -> str:
    """Converte YYYY-MM-DD ou YYYYMMDD para D(8) YYYYMMDD."""
    if not value:
        return " " * 8
    cleaned = str(value).strip().replace("-", "").replace("/", "")
    if len(cleaned) >= 8 and cleaned[:8].isdigit():
        return cleaned[:8]
    return " " * 8


def parse_date_dbf(raw: str) -> Optional[str]:
    """Converte D(8) YYYYMMDD para ISO YYYY-MM-DD."""
    cleaned = raw.strip()
    if len(cleaned) == 8 and cleaned.isdigit():
        return f"{cleaned[0:4]}-{cleaned[4:6]}-{cleaned[6:8]}"
    return None

