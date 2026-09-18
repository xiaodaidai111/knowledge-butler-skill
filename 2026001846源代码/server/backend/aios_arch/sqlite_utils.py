"""Small SQLite helpers shared by the AIOS persistence adapters."""
from __future__ import annotations

import sqlite3
from pathlib import Path


class ClosingConnection(sqlite3.Connection):
    """Commit or roll back, then release the Windows file handle immediately."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=30, factory=ClosingConnection)
    connection.execute("PRAGMA busy_timeout=30000")
    return connection
