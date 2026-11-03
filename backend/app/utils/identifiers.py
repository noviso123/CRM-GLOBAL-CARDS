import os
import time
import uuid


def generate_id() -> str:
    """Gera um identificador UUIDv7-like estável e ordenável por tempo (36 caracteres)."""
    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
    uuid_int = (ts_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    return str(uuid.UUID(int=uuid_int))


def generate_code(prefix: str, sequence_num: int, width: int = 5) -> str:
    """Gera um código comercial legível (ex: CLI-00001, PED-00042)."""
    return f"{prefix.upper()}-{sequence_num:0{width}d}"

