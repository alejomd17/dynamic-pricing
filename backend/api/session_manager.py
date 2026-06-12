"""
Session Manager - Maneja el estado de las sesiones
"""

import pickle
import uuid
from pathlib import Path
from typing import Optional, Any
import pandas as pd


class SessionManager:
    """
    Maneja sesiones de usuario y sus datos
    """

    def __init__(self, sessions_dir: str = "data/sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self) -> str:
        """Crea una nueva sesión y retorna el ID"""
        session_id = str(uuid.uuid4())[:8]
        session_path = self.sessions_dir / session_id
        session_path.mkdir(exist_ok=True)
        return session_id

    def get_session_path(self, session_id: str) -> Path:
        """Obtiene el path de una sesión"""
        return self.sessions_dir / session_id

    def session_exists(self, session_id: str) -> bool:
        """Verifica si existe una sesión"""
        return self.get_session_path(session_id).exists()

    def save_dataframe(self, session_id: str, df: pd.DataFrame, name: str = "df"):
        """Guarda un DataFrame en la sesión"""
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")

        path = self.get_session_path(session_id) / f"{name}.parquet"
        df.to_parquet(path)

    def load_dataframe(self, session_id: str, name: str = "df") -> pd.DataFrame:
        """Carga un DataFrame de la sesión"""
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")

        path = self.get_session_path(session_id) / f"{name}.parquet"
        if not path.exists():
            raise FileNotFoundError(
                f"DataFrame '{name}' not found in session {session_id}"
            )

        return pd.read_parquet(path)

    def save_object(self, session_id: str, obj: Any, name: str):
        """Guarda un objeto Python en la sesión"""
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")

        path = self.get_session_path(session_id) / f"{name}.pkl"
        with open(path, "wb") as f:
            pickle.dump(obj, f)

    def load_object(self, session_id: str, name: str) -> Any:
        """Carga un objeto Python de la sesión"""
        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")

        path = self.get_session_path(session_id) / f"{name}.pkl"
        if not path.exists():
            raise FileNotFoundError(
                f"Object '{name}' not found in session {session_id}"
            )

        with open(path, "rb") as f:
            return pickle.load(f)

    def save_metadata(self, session_id: str, metadata: dict):
        """Guarda metadata de la sesión"""
        import json

        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")

        path = self.get_session_path(session_id) / "metadata.json"
        with open(path, "w") as f:
            json.dump(metadata, f)

    def get_latest_session(self) -> Optional[str]:
        """Retorna el ID de la sesión más reciente, o None si no hay ninguna"""
        sessions = [p for p in self.sessions_dir.iterdir() if p.is_dir()]
        if not sessions:
            return None
        latest = max(sessions, key=lambda p: p.stat().st_mtime)
        return latest.name

    def load_metadata(self, session_id: str) -> dict:
        """Carga metadata de la sesión"""
        import json

        if not self.session_exists(session_id):
            raise ValueError(f"Session {session_id} does not exist")

        path = self.get_session_path(session_id) / "metadata.json"
        if not path.exists():
            return {}

        with open(path, "r") as f:
            return json.load(f)
