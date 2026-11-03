import datetime
import os
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from app.core.exceptions import DBFStorageError
from app.database.dbf_schema import DBFFieldDef, DBFTableSchema
from app.utils.dates import format_date_dbf, parse_date_dbf

ENCODING = "cp1252"
STRICT_FSYNC = os.getenv("SATIRO_STRICT_FSYNC", "0") == "1"


def _sync_file(f) -> None:
    f.flush()
    if STRICT_FSYNC:
        os.fsync(f.fileno())



class DBFTableConnection:
    """Manipulador binário direto de arquivos dBase III+ (0x03) com flag de transação no Byte 14 e CP1252 seguro."""

    def __init__(self, dbf_path: Path, schema: DBFTableSchema):
        self.dbf_path = dbf_path
        self.schema = schema

    def ensure_file_exists(self) -> None:
        self.dbf_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.dbf_path.exists():
            self._create_empty_dbf()
        else:
            self.verify_header()

    def _create_empty_dbf(self) -> None:
        today = datetime.date.today()
        header = bytearray(32)
        header[0] = 0x03  # dBase III+
        header[1] = today.year - 1900
        header[2] = today.month
        header[3] = today.day
        struct.pack_into("<I", header, 4, 0)  # 0 records
        struct.pack_into("<H", header, 8, self.schema.header_length)
        struct.pack_into("<H", header, 10, self.schema.record_length)
        header[14] = 0x00  # Incomplete transaction flag = clean
        header[29] = 0x57  # ANSI / Windows-1252 Language Driver

        field_descriptors = bytearray()
        for fdef in self.schema.fields:
            name_bytes = fdef.name.encode("ascii")[:10].ljust(11, b"\x00")
            desc = struct.pack(
                "<11s c 4s B B 14s",
                name_bytes,
                fdef.ftype.encode("ascii"),
                b"\x00" * 4,
                fdef.length,
                fdef.decimals,
                b"\x00" * 14,
            )
            field_descriptors.extend(desc)

        with open(self.dbf_path, "wb") as f:
            f.write(header)
            f.write(field_descriptors)
            f.write(b"\x0d")  # Header terminator
            f.write(b"\x1a")  # EOF marker
            _sync_file(f)

    def verify_header(self) -> Dict[str, Any]:
        if not self.dbf_path.exists():
            raise DBFStorageError(f"Arquivo {self.dbf_path.name} não encontrado.")
        with open(self.dbf_path, "rb") as f:
            raw = f.read(32)
            if len(raw) < 32 or raw[0] != 0x03:
                raise DBFStorageError(
                    f"Cabeçalho DBF inválido ou corrompido em {self.dbf_path.name}."
                )
            num_records = struct.unpack_from("<I", raw, 4)[0]
            header_len = struct.unpack_from("<H", raw, 8)[0]
            record_len = struct.unpack_from("<H", raw, 10)[0]
            tx_flag = raw[14]
            if header_len != self.schema.header_length or record_len != self.schema.record_length:
                raise DBFStorageError(
                    f"Incompatibilidade de estrutura binária em {self.dbf_path.name}."
                )
        # Se houve interrupção anterior (tx_flag == 1), recalcula o número real de registros pelo tamanho do arquivo
        if tx_flag == 0x01:
            self._recover_interrupted_file()
        return {
            "table": self.schema.name,
            "num_records": num_records,
            "header_length": header_len,
            "record_length": record_len,
            "tx_flag": tx_flag,
        }

    def _recover_interrupted_file(self) -> None:
        file_size = self.dbf_path.stat().st_size
        data_bytes = max(0, file_size - self.schema.header_length - 1)
        actual_records = data_bytes // self.schema.record_length
        today = datetime.date.today()
        with open(self.dbf_path, "r+b") as f:
            f.seek(1)
            f.write(bytes([today.year - 1900, today.month, today.day]))
            f.write(struct.pack("<I", actual_records))
            f.seek(14)
            f.write(b"\x00")
            f.seek(self.schema.header_length + actual_records * self.schema.record_length)
            f.write(b"\x1a")
            f.truncate()
            f.flush()
            os.fsync(f.fileno())

    def encode_field(self, fdef: DBFFieldDef, value: Any) -> bytes:
        if value is None:
            value = fdef.default
        if fdef.ftype == "C":
            text = "" if value is None else str(value)
            encoded = text.encode(ENCODING, errors="replace")[: fdef.length]
            return encoded.ljust(fdef.length, b" ")
        if fdef.ftype == "N":
            num = 0.0 if value is None or value == "" else float(value)
            if fdef.decimals == 0:
                formatted = f"{int(round(num)):>{fdef.length}d}"
            else:
                formatted = f"{num:>{fdef.length}.{fdef.decimals}f}"
            raw = formatted.encode("ascii")
            if len(raw) > fdef.length:
                raw = raw[-fdef.length :]
            return raw.rjust(fdef.length, b" ")
        if fdef.ftype == "D":
            d_str = format_date_dbf(str(value) if value else None)
            return d_str.encode("ascii")[:8].ljust(8, b" ")
        if fdef.ftype == "L":
            if isinstance(value, str):
                b_val = value.strip().upper() in ("T", "Y", "1", "TRUE", "SIM")
            else:
                b_val = bool(value)
            return b"T" if b_val else b"F"
        raise DBFStorageError(f"Tipo de campo DBF desconhecido: {fdef.ftype}")

    def decode_field(self, fdef: DBFFieldDef, raw_bytes: bytes) -> Any:
        if fdef.ftype == "C":
            return raw_bytes.decode(ENCODING, errors="replace").rstrip(" ")
        if fdef.ftype == "N":
            txt = raw_bytes.decode("ascii", errors="replace").strip()
            if not txt:
                return 0 if fdef.decimals == 0 else 0.0
            try:
                return int(float(txt)) if fdef.decimals == 0 else round(float(txt), fdef.decimals)
            except ValueError:
                return 0 if fdef.decimals == 0 else 0.0
        if fdef.ftype == "D":
            txt = raw_bytes.decode("ascii", errors="replace")
            return parse_date_dbf(txt) or ""
        if fdef.ftype == "L":
            ch = raw_bytes.decode("ascii", errors="replace").strip().upper()
            return ch in ("T", "Y")
        return None

    def serialize_record(self, data: Dict[str, Any], deleted: bool = False) -> bytes:
        buf = bytearray()
        buf.append(0x2A if deleted else 0x20)
        for fdef in self.schema.fields:
            buf.extend(self.encode_field(fdef, data.get(fdef.name)))
        return bytes(buf)

    def deserialize_record(self, raw_record: bytes) -> Tuple[bool, Dict[str, Any]]:
        if len(raw_record) < self.schema.record_length:
            raise DBFStorageError("Registro DBF truncado.")
        deleted = raw_record[0] == 0x2A
        offset = 1
        record: Dict[str, Any] = {}
        for fdef in self.schema.fields:
            slice_bytes = raw_record[offset : offset + fdef.length]
            record[fdef.name] = self.decode_field(fdef, slice_bytes)
            offset += fdef.length
        return deleted, record

    def append_record(self, data: Dict[str, Any]) -> int:
        raw_rec = self.serialize_record(data, deleted=False)
        today = datetime.date.today()
        with open(self.dbf_path, "r+b") as f:
            f.seek(4)
            num_records = struct.unpack("<I", f.read(4))[0]
            # Marca início de transação no Byte 14
            f.seek(14)
            f.write(b"\x01")
            f.flush()

            rec_offset = self.schema.header_length + (num_records * self.schema.record_length)
            f.seek(rec_offset)
            f.write(raw_rec)
            f.write(b"\x1a")

            new_total = num_records + 1
            f.seek(1)
            f.write(bytes([today.year - 1900, today.month, today.day]))
            f.write(struct.pack("<I", new_total))
            f.seek(14)
            f.write(b"\x00")
            _sync_file(f)
            return num_records

    def read_record_at(self, rec_index: int) -> Optional[Dict[str, Any]]:
        with open(self.dbf_path, "rb") as f:
            f.seek(4)
            num_records = struct.unpack("<I", f.read(4))[0]
            if rec_index < 0 or rec_index >= num_records:
                return None
            rec_offset = self.schema.header_length + (rec_index * self.schema.record_length)
            f.seek(rec_offset)
            raw = f.read(self.schema.record_length)
            if len(raw) < self.schema.record_length:
                return None
            deleted, record = self.deserialize_record(raw)
            if deleted:
                return None
            return record

    def update_record_at(self, rec_index: int, data: Dict[str, Any]) -> None:
        raw_rec = self.serialize_record(data, deleted=False)
        today = datetime.date.today()
        with open(self.dbf_path, "r+b") as f:
            f.seek(4)
            num_records = struct.unpack("<I", f.read(4))[0]
            if rec_index < 0 or rec_index >= num_records:
                raise DBFStorageError("Índice físico de registro inválido para atualização.")
            f.seek(14)
            f.write(b"\x01")
            rec_offset = self.schema.header_length + (rec_index * self.schema.record_length)
            f.seek(rec_offset)
            f.write(raw_rec)
            f.seek(1)
            f.write(bytes([today.year - 1900, today.month, today.day]))
            f.seek(14)
            f.write(b"\x00")
            _sync_file(f)

    def mark_deleted_at(self, rec_index: int) -> bool:
        today = datetime.date.today()
        with open(self.dbf_path, "r+b") as f:
            f.seek(4)
            num_records = struct.unpack("<I", f.read(4))[0]
            if rec_index < 0 or rec_index >= num_records:
                return False
            rec_offset = self.schema.header_length + (rec_index * self.schema.record_length)
            f.seek(rec_offset)
            flag = f.read(1)
            if flag == b"\x2a":
                return False
            f.seek(14)
            f.write(b"\x01")
            f.seek(rec_offset)
            f.write(b"\x2a")
            f.seek(1)
            f.write(bytes([today.year - 1900, today.month, today.day]))
            f.seek(14)
            f.write(b"\x00")
            _sync_file(f)
            return True

    def iter_active_records(self) -> List[Tuple[int, Dict[str, Any]]]:
        results: List[Tuple[int, Dict[str, Any]]] = []
        with open(self.dbf_path, "rb") as f:
            f.seek(4)
            num_records = struct.unpack("<I", f.read(4))[0]
            f.seek(self.schema.header_length)
            for idx in range(num_records):
                raw = f.read(self.schema.record_length)
                if len(raw) < self.schema.record_length:
                    break
                deleted, rec = self.deserialize_record(raw)
                if not deleted:
                    results.append((idx, rec))
        return results

    def pack(self) -> Dict[str, int]:
        """Remove fisicamente registros marcados com '*' (0x2A) de forma atômica."""
        with open(self.dbf_path, "rb") as f:
            header_bytes = bytearray(f.read(self.schema.header_length))
            total_before = struct.unpack_from("<I", header_bytes, 4)[0]
            active_raws: List[bytes] = []
            for _ in range(total_before):
                raw = f.read(self.schema.record_length)
                if len(raw) == self.schema.record_length and raw[0] != 0x2A:
                    active_raws.append(raw)

        today = datetime.date.today()
        header_bytes[1] = today.year - 1900
        header_bytes[2] = today.month
        header_bytes[3] = today.day
        struct.pack_into("<I", header_bytes, 4, len(active_raws))
        header_bytes[14] = 0x00

        tmp_path = self.dbf_path.with_suffix(".DBF.TMP")
        with open(tmp_path, "wb") as f:
            f.write(header_bytes)
            for r in active_raws:
                f.write(r)
            f.write(b"\x1a")
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, self.dbf_path)
        return {
            "total_before": total_before,
            "active_records": len(active_raws),
            "removed_records": total_before - len(active_raws),
        }
