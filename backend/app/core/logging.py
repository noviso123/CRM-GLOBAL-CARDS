import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from app.core.config import settings


def setup_logging(logs_dir: Optional[Path] = None) -> logging.Logger:
    target_dir = logs_dir or settings.logs_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    log_file = target_dir / "satiro_crm.log"

    logger = logging.getLogger("crm_satiro")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger


def write_audit_log(
    action: str,
    entity: str,
    record_id: str,
    user_id: str = "SYSTEM",
    result: str = "SUCCESS",
    metadata: Optional[Dict[str, Any]] = None,
    logs_dir: Optional[Path] = None,
) -> None:
    target_dir = logs_dir or settings.logs_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    audit_file = target_dir / "audit.jsonl"
    safe_meta = {}
    if metadata:
        for k, v in metadata.items():
            if any(sec in k.lower() for sec in ("senha", "password", "token", "secret", "hash")):
                continue
            safe_meta[k] = v
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "user_id": user_id,
        "entity": entity,
        "record_id": record_id,
        "action": action,
        "result": result,
        "metadata": safe_meta,
    }
    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

