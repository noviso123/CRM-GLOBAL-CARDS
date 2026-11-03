import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from app.core.exceptions import DBFStorageError, NotFoundErrorCRM
from app.database.dbf_manager import DBFManager
from app.database.dbf_schema import ALL_TABLES


class BackupManager:
    """Gerencia backups consistentes dos 21 arquivos DBF, índices, documentos e anexos com verificação SHA-256."""

    def __init__(self, manager: DBFManager):
        self.mgr = manager

    @staticmethod
    def _sha256_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def create_backup(self, description: str = "Backup automático/manual") -> Dict[str, Any]:
        with self.mgr.locks.global_lock():
            self.mgr.initialize_all_tables()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_id = f"backup_{ts}"
            zip_path = self.mgr.backups_dir / f"{backup_id}.zip"

            manifest_files: Dict[str, Dict[str, Any]] = {}
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for tname in ALL_TABLES:
                    dbf_file = self.mgr.dbf_dir / f"{tname}.DBF"
                    conn = self.mgr.get_connection(tname)
                    hdr = conn.verify_header()
                    active = len(conn.iter_active_records())
                    arcname = f"dbf/{tname}.DBF"
                    zf.write(dbf_file, arcname=arcname)
                    manifest_files[arcname] = {
                        "sha256": self._sha256_file(dbf_file),
                        "size_bytes": dbf_file.stat().st_size,
                        "total_records": hdr["num_records"],
                        "active_records": active,
                    }

                for folder_name, folder_path in (
                    ("indexes", self.mgr.indexes_dir),
                    ("documents", self.mgr.documents_dir),
                    ("attachments", self.mgr.attachments_dir),
                ):
                    if folder_path.exists():
                        for file_path in folder_path.rglob("*"):
                            if file_path.is_file() and not file_path.name.endswith(".TMP"):
                                rel = file_path.relative_to(self.mgr.base_dir).as_posix()
                                zf.write(file_path, arcname=rel)
                                manifest_files[rel] = {
                                    "sha256": self._sha256_file(file_path),
                                    "size_bytes": file_path.stat().st_size,
                                }

                manifest = {
                    "backup_id": backup_id,
                    "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    "description": description,
                    "tables_count": len(ALL_TABLES),
                    "files": manifest_files,
                }
                zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

            return {
                "backup_id": backup_id,
                "zip_path": str(zip_path),
                "created_at": manifest["created_at"],
                "description": description,
                "tables_count": len(ALL_TABLES),
                "size_bytes": zip_path.stat().st_size,
            }

    def list_backups(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        if not self.mgr.backups_dir.exists():
            return results
        for zp in sorted(self.mgr.backups_dir.glob("backup_*.zip"), reverse=True):
            try:
                with zipfile.ZipFile(zp, "r") as zf:
                    manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                results.append(
                    {
                        "backup_id": manifest.get("backup_id", zp.stem),
                        "created_at": manifest.get("created_at", ""),
                        "description": manifest.get("description", ""),
                        "tables_count": manifest.get("tables_count", 21),
                        "size_bytes": zp.stat().st_size,
                    }
                )
            except Exception:
                continue
        return results

    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        zip_path = self.mgr.backups_dir / f"{backup_id}.zip"
        if not zip_path.exists():
            raise NotFoundErrorCRM("BACKUP", backup_id)

        with self.mgr.locks.global_lock():
            staging_dir = self.mgr.backups_dir / f"_restore_stage_{backup_id}"
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)
            staging_dir.mkdir(parents=True, exist_ok=True)

            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    if "manifest.json" not in zf.namelist():
                        raise DBFStorageError("Arquivo de backup inválido: manifest.json ausente.")
                    manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
                    zf.extractall(staging_dir)

                for rel_path, meta in manifest.get("files", {}).items():
                    extracted_file = staging_dir / rel_path
                    if not extracted_file.exists():
                        raise DBFStorageError(f"Arquivo esperado ausente no backup: {rel_path}")
                    actual_hash = self._sha256_file(extracted_file)
                    if actual_hash != meta.get("sha256"):
                        raise DBFStorageError(
                            f"Falha de integridade SHA-256 ao validar {rel_path} no backup."
                        )

                # Copia os DBFs, documentos e anexos restaurados para os diretórios oficiais
                for sub in ("dbf", "documents", "attachments"):
                    src_sub = staging_dir / sub
                    dst_sub = self.mgr.base_dir / sub
                    if src_sub.exists():
                        dst_sub.mkdir(parents=True, exist_ok=True)
                        for item in src_sub.rglob("*"):
                            if item.is_file():
                                rel_item = item.relative_to(src_sub)
                                target_path = dst_sub / rel_item
                                target_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(item, target_path)

                rebuilt_counts = self.mgr.rebuild_all_indexes()
                return {
                    "restored": True,
                    "backup_id": backup_id,
                    "tables_restored": len(rebuilt_counts),
                    "active_records_by_table": rebuilt_counts,
                }
            finally:
                shutil.rmtree(staging_dir, ignore_errors=True)

