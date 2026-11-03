import json
import zlib
from pathlib import Path
from typing import Dict, List
from app.database.dbf_schema import DBFTableSchema


class IndexManager:
    """Gerencia índices secundários persistentes (.IDX) com verificação de integridade CRC32."""

    def __init__(self, indexes_dir: Path):
        self.indexes_dir = indexes_dir
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        # Estrutura em memória: {table_name: {field_name: {normalized_val: [rec_index, ...]}}}
        self._cache: Dict[str, Dict[str, Dict[str, List[int]]]] = {}

    @staticmethod
    def normalize_key(value: object) -> str:
        if value is None:
            return ""
        return str(value).strip().upper()

    def _idx_path(self, table_name: str) -> Path:
        return self.indexes_dir / f"{table_name.upper()}.IDX"

    def init_table_index(self, schema: DBFTableSchema) -> None:
        tname = schema.name.upper()
        if tname not in self._cache:
            idx_file = self._idx_path(tname)
            if idx_file.exists():
                loaded = self._load_from_disk(idx_file)
                if loaded is not None:
                    self._cache[tname] = loaded
                    return
            self._cache[tname] = {f: {} for f in schema.indexed_fields}
            self._save_to_disk(tname)

    def _load_from_disk(self, idx_file: Path) -> Dict[str, Dict[str, List[int]]] | None:
        try:
            with open(idx_file, "r", encoding="utf-8") as f:
                wrapper = json.load(f)
            payload_str = json.dumps(wrapper["data"], sort_keys=True)
            crc = zlib.crc32(payload_str.encode("utf-8")) & 0xFFFFFFFF
            if crc != wrapper.get("crc32"):
                return None
            return wrapper["data"]
        except Exception:
            return None

    def _save_to_disk(self, table_name: str) -> None:
        tname = table_name.upper()
        data = self._cache.get(tname, {})
        payload_str = json.dumps(data, sort_keys=True)
        crc = zlib.crc32(payload_str.encode("utf-8")) & 0xFFFFFFFF
        wrapper = {"table": tname, "crc32": crc, "data": data}
        idx_file = self._idx_path(tname)
        tmp_file = idx_file.with_suffix(".IDX.TMP")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(wrapper, f, ensure_ascii=False)
        tmp_file.replace(idx_file)

    def index_record(
        self, schema: DBFTableSchema, rec_index: int, record: Dict[str, object], flush: bool = True
    ) -> None:
        tname = schema.name.upper()
        if tname not in self._cache:
            self.init_table_index(schema)
        table_idx = self._cache[tname]
        for field_name in schema.indexed_fields:
            field_map = table_idx.setdefault(field_name, {})
            key = self.normalize_key(record.get(field_name, ""))
            bucket = field_map.setdefault(key, [])
            if rec_index not in bucket:
                bucket.append(rec_index)
        if flush:
            self._save_to_disk(tname)

    def unindex_record(
        self, schema: DBFTableSchema, rec_index: int, record: Dict[str, object], flush: bool = True
    ) -> None:
        tname = schema.name.upper()
        if tname not in self._cache:
            return
        table_idx = self._cache[tname]
        for field_name in schema.indexed_fields:
            field_map = table_idx.get(field_name, {})
            key = self.normalize_key(record.get(field_name, ""))
            if key in field_map and rec_index in field_map[key]:
                field_map[key].remove(rec_index)
                if not field_map[key]:
                    del field_map[key]
        if flush:
            self._save_to_disk(tname)

    def lookup(self, table_name: str, field_name: str, value: object) -> List[int]:
        tname = table_name.upper()
        fname = field_name.upper()
        key = self.normalize_key(value)
        return list(self._cache.get(tname, {}).get(fname, {}).get(key, []))

    def rebuild_table_index(
        self, schema: DBFTableSchema, active_records_with_idx: List[ tuple[int, Dict[str, object]] ]
    ) -> None:
        tname = schema.name.upper()
        self._cache[tname] = {f: {} for f in schema.indexed_fields}
        for rec_idx, rec in active_records_with_idx:
            self.index_record(schema, rec_idx, rec, flush=False)
        self._save_to_disk(tname)

