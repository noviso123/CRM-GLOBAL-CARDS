import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Dict
from filelock import FileLock, Timeout
from app.core.exceptions import DBFStorageError


class LockManager:
    """Gerencia bloqueios em memória (RLock) e em disco (FileLock) por tabela e globalmente."""

    def __init__(self, locks_dir: Path):
        self.locks_dir = locks_dir
        self.locks_dir.mkdir(parents=True, exist_ok=True)
        self._guard = threading.RLock()
        self._thread_locks: Dict[str, threading.RLock] = {}
        self._file_locks: Dict[str, FileLock] = {}

    def _get_locks(self, name: str):
        with self._guard:
            if name not in self._thread_locks:
                self._thread_locks[name] = threading.RLock()
                lock_path = self.locks_dir / f"{name}.lock"
                self._file_locks[name] = FileLock(str(lock_path), timeout=15)
            return self._thread_locks[name], self._file_locks[name]

    @contextmanager
    def table_lock(self, table_name: str):
        t_lock, f_lock = self._get_locks(table_name.upper())
        with t_lock:
            try:
                with f_lock:
                    yield
            except Timeout as exc:
                raise DBFStorageError(
                    f"Tempo limite excedido aguardando bloqueio do arquivo {table_name}.DBF."
                ) from exc

    @contextmanager
    def global_lock(self):
        t_lock, f_lock = self._get_locks("_GLOBAL_BACKUP_LOCK_")
        with t_lock:
            try:
                with f_lock:
                    yield
            except Timeout as exc:
                raise DBFStorageError(
                    "Tempo limite excedido aguardando bloqueio global dos arquivos DBF."
                ) from exc

