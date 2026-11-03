import json
from pathlib import Path
from typing import Any, Dict, Optional


def save_external_document(
    base_data_dir: Path, domain: str, record_id: str, payload: Dict[str, Any]
) -> str:
    """Salva textos extensos, observações detalhadas ou metadados de galeria fora do DBF e retorna o caminho relativo."""
    rel_path = f"documents/{domain}/{record_id}.json"
    full_path = base_data_dir / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return rel_path


def load_external_document(
    base_data_dir: Path, rel_path: Optional[str]
) -> Dict[str, Any]:
    """Carrega documento JSON externo referenciado pelo campo DOC_REF do DBF."""
    if not rel_path or not rel_path.strip():
        return {}
    safe_rel = Path(rel_path.strip())
    if safe_rel.is_absolute() or ".." in safe_rel.parts:
        return {}
    full_path = base_data_dir / safe_rel
    if not full_path.exists():
        return {}
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

