from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from app.core.config import settings
from app.core.exceptions import DBFStorageError, IntegrityErrorCRM, ValidationErrorCRM
from app.database.dbf_connection import DBFTableConnection
from app.database.dbf_schema import ALL_SCHEMAS, ALL_TABLES, DBFTableSchema
from app.database.indexes import IndexManager
from app.database.locks import LockManager
from app.utils.dates import now_iso, today_dbf
from app.utils.identifiers import generate_id


class DBFManager:
    """Gerenciador central de acesso aos 21 arquivos DBF, índices .IDX e bloqueios de concorrência."""

    def __init__(self, base_data_dir: Optional[Path] = None):
        self.base_dir = base_data_dir or settings.data_dir
        self.dbf_dir = self.base_dir / "dbf"
        self.indexes_dir = self.base_dir / "indexes"
        self.documents_dir = self.base_dir / "documents"
        self.attachments_dir = self.base_dir / "attachments"
        self.backups_dir = self.base_dir / "backups"
        self.locks_dir = self.base_dir / "locks"

        for d in (
            self.dbf_dir,
            self.indexes_dir,
            self.documents_dir,
            self.attachments_dir,
            self.backups_dir,
            self.locks_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

        self.locks = LockManager(self.locks_dir)
        self.indexes = IndexManager(self.indexes_dir)
        self._connections: Dict[str, DBFTableConnection] = {}

    def get_schema(self, table_name: str) -> DBFTableSchema:
        tname = table_name.upper()
        if tname not in ALL_SCHEMAS:
            raise DBFStorageError(f"Tabela DBF desconhecida: {tname}")
        return ALL_SCHEMAS[tname]

    def get_connection(self, table_name: str) -> DBFTableConnection:
        tname = table_name.upper()
        if tname not in self._connections:
            schema = self.get_schema(tname)
            dbf_path = self.dbf_dir / f"{tname}.DBF"
            conn = DBFTableConnection(dbf_path, schema)
            self._connections[tname] = conn
        return self._connections[tname]

    def initialize_all_tables(self) -> None:
        with self.locks.global_lock():
            for tname in ALL_TABLES:
                schema = self.get_schema(tname)
                conn = self.get_connection(tname)
                conn.ensure_file_exists()
                active = conn.iter_active_records()
                self.indexes.rebuild_table_index(schema, active)

    def _prepare_insert_record(
        self, schema: DBFTableSchema, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        now = now_iso()
        record: Dict[str, Any] = {}
        field_names = {f.name for f in schema.fields}

        for fdef in schema.fields:
            val = payload.get(fdef.name)
            if val is None or val == "":
                if fdef.name == "ID":
                    val = generate_id()
                elif fdef.name in ("DT_CRIA", "DT_ATUA", "DT_ENVIO"):
                    val = now
                elif fdef.ftype == "D" and fdef.required:
                    val = today_dbf()
                elif fdef.name == "VERSAO":
                    val = 1
                else:
                    val = fdef.default
            record[fdef.name] = val

            if fdef.required and (record[fdef.name] is None or str(record[fdef.name]).strip() == ""):
                raise ValidationErrorCRM(
                    f"Campo obrigatório '{fdef.name}' não informado na tabela {schema.name}.",
                    details={"table": schema.name, "field": fdef.name},
                )

        if "DT_ATUA" in field_names and not payload.get("DT_ATUA"):
            record["DT_ATUA"] = now
        return record

    def _check_uniqueness(
        self, schema: DBFTableSchema, record: Dict[str, Any], exclude_id: Optional[str] = None
    ) -> None:
        for u_field in schema.unique_fields:
            val = record.get(u_field)
            if val is None or str(val).strip() == "":
                continue
            matches = self.find_by_field(schema.name, u_field, val)
            for m in matches:
                if exclude_id and m.get("ID") == exclude_id:
                    continue
                raise IntegrityErrorCRM(
                    f"Já existe um registro em {schema.name} com {u_field} = '{val}'.",
                    details={"table": schema.name, "field": u_field, "value": val},
                )

    def insert(self, table_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        schema = self.get_schema(table_name)
        conn = self.get_connection(table_name)
        with self.locks.table_lock(schema.name):
            conn.ensure_file_exists()
            record = self._prepare_insert_record(schema, payload)
            self._check_uniqueness(schema, record)
            rec_idx = conn.append_record(record)
            saved = conn.read_record_at(rec_idx) or record
            self.indexes.index_record(schema, rec_idx, saved, flush=True)
            return saved

    def get_by_id(self, table_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        if not record_id:
            return None
        matches = self.find_by_field(table_name, "ID", record_id)
        return matches[0] if matches else None

    def find_by_field(
        self, table_name: str, field_name: str, value: Any
    ) -> List[Dict[str, Any]]:
        schema = self.get_schema(table_name)
        conn = self.get_connection(table_name)
        fname = field_name.upper()
        with self.locks.table_lock(schema.name):
            conn.ensure_file_exists()
            if fname in schema.indexed_fields:
                positions = self.indexes.lookup(schema.name, fname, value)
                results: List[Dict[str, Any]] = []
                for pos in positions:
                    rec = conn.read_record_at(pos)
                    if rec is not None and IndexManager.normalize_key(rec.get(fname)) == IndexManager.normalize_key(value):
                        results.append(rec)
                return results

            target = IndexManager.normalize_key(value)
            return [
                rec
                for _, rec in conn.iter_active_records()
                if IndexManager.normalize_key(rec.get(fname)) == target
            ]

    def find_all(
        self,
        table_name: str,
        predicate: Optional[Callable[[Dict[str, Any]], bool]] = None,
        sort_by: Optional[str] = None,
        descending: bool = False,
    ) -> List[Dict[str, Any]]:
        schema = self.get_schema(table_name)
        conn = self.get_connection(table_name)
        with self.locks.table_lock(schema.name):
            conn.ensure_file_exists()
            rows = [rec for _, rec in conn.iter_active_records()]
        if predicate:
            rows = [r for r in rows if predicate(r)]
        if sort_by:
            rows.sort(key=lambda r: (r.get(sort_by) is None, r.get(sort_by, "")), reverse=descending)
        return rows

    def update(
        self, table_name: str, record_id: str, changes: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        schema = self.get_schema(table_name)
        conn = self.get_connection(table_name)
        with self.locks.table_lock(schema.name):
            conn.ensure_file_exists()
            positions = self.indexes.lookup(schema.name, "ID", record_id)
            target_pos: Optional[int] = None
            old_rec: Optional[Dict[str, Any]] = None
            for pos in positions:
                rec = conn.read_record_at(pos)
                if rec and rec.get("ID") == record_id:
                    target_pos = pos
                    old_rec = rec
                    break
            if target_pos is None or old_rec is None:
                return None

            updated = dict(old_rec)
            for k, v in changes.items():
                k_up = k.upper()
                if k_up != "ID" and any(f.name == k_up for f in schema.fields):
                    if v is not None:
                        updated[k_up] = v

            if any(f.name == "DT_ATUA" for f in schema.fields):
                updated["DT_ATUA"] = now_iso()
            if any(f.name == "VERSAO" for f in schema.fields):
                updated["VERSAO"] = int(old_rec.get("VERSAO", 1)) + 1

            self._check_uniqueness(schema, updated, exclude_id=record_id)
            self.indexes.unindex_record(schema, target_pos, old_rec, flush=False)
            conn.update_record_at(target_pos, updated)
            saved = conn.read_record_at(target_pos) or updated
            self.indexes.index_record(schema, target_pos, saved, flush=True)
            return saved

    def delete(self, table_name: str, record_id: str) -> bool:
        schema = self.get_schema(table_name)
        conn = self.get_connection(table_name)
        with self.locks.table_lock(schema.name):
            conn.ensure_file_exists()
            positions = self.indexes.lookup(schema.name, "ID", record_id)
            for pos in positions:
                rec = conn.read_record_at(pos)
                if rec and rec.get("ID") == record_id:
                    self.indexes.unindex_record(schema, pos, rec, flush=True)
                    return conn.mark_deleted_at(pos)
            return False

    def pack_table(self, table_name: str) -> Dict[str, int]:
        schema = self.get_schema(table_name)
        conn = self.get_connection(table_name)
        with self.locks.table_lock(schema.name):
            conn.ensure_file_exists()
            stats = conn.pack()
            active = conn.iter_active_records()
            self.indexes.rebuild_table_index(schema, active)
            return stats

    def rebuild_all_indexes(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        with self.locks.global_lock():
            for tname in ALL_TABLES:
                schema = self.get_schema(tname)
                conn = self.get_connection(tname)
                conn.ensure_file_exists()
                active = conn.iter_active_records()
                self.indexes.rebuild_table_index(schema, active)
                counts[tname] = len(active)
        return counts

    def verify_all_tables_integrity(self) -> List[Dict[str, Any]]:
        report: List[Dict[str, Any]] = []
        with self.locks.global_lock():
            for tname in ALL_TABLES:
                conn = self.get_connection(tname)
                conn.ensure_file_exists()
                hdr = conn.verify_header()
                active = conn.iter_active_records()
                hdr["active_records"] = len(active)
                hdr["deleted_records"] = hdr["num_records"] - len(active)
                hdr["status"] = "OK"
                report.append(hdr)
        return report

    def next_sequence_code(self, table_name: str, prefix: str) -> str:
        conn = self.get_connection(table_name)
        with self.locks.table_lock(table_name):
            conn.ensure_file_exists()
            hdr = conn.verify_header()
            seq = hdr["num_records"] + 1
            return f"{prefix.upper()}-{seq:05d}"


dbf_manager = DBFManager()

