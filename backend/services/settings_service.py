import os
from pathlib import Path
from cryptography.fernet import Fernet
from backend.storage.db import cur, conn

class SettingsService:
    def __init__(self):
        self._cipher = self._get_cipher()
    
    def _get_key_path(self):
        """Get the path to the encryption key file"""
        from backend.config import get_data_dir
        return get_data_dir() / ".forge_key"
    
    def _get_cipher(self):
        key = os.getenv("FORGE_ENCRYPTION_KEY")
        if not key:
            key_file = self._get_key_path()
            if key_file.exists():
                with open(key_file, "rb") as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(key)
                try:
                    os.chmod(key_file, 0o600)
                except Exception:
                    pass
        else:
            key = key.encode()
        return Fernet(key)
    
    def _encrypt(self, value: str) -> str:
        return self._cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, encrypted_value: str) -> str:
        return self._cipher.decrypt(encrypted_value.encode()).decode()
    
    def get_setting(self, key: str, encrypted: bool = False) -> str | None:
        row = cur.execute("SELECT v FROM kv WHERE k=?", (f"setting_{key}",)).fetchone()
        if not row:
            return None
        value = row[0]
        if encrypted:
            try:
                return self._decrypt(value)
            except Exception:
                return None
        return value
    
    def set_setting(self, key: str, value: str, encrypted: bool = False):
        if encrypted:
            value = self._encrypt(value)
        cur.execute(
            "INSERT INTO kv (k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
            (f"setting_{key}", value)
        )
        conn.commit()
    
    def delete_setting(self, key: str):
        cur.execute("DELETE FROM kv WHERE k=?", (f"setting_{key}",))
        conn.commit()
    
    def get_lmstudio_url(self) -> str:
        from backend.config import settings
        db_value = self.get_setting("lmstudio_url")
        env_value = os.getenv("LMSTUDIO_BASE_URL")
        return db_value or env_value or settings.LMSTUDIO_BASE_URL
    
    def get_openai_api_key(self) -> str | None:
        db_value = self.get_setting("openai_api_key", encrypted=True)
        env_value = os.getenv("OPENAI_API_KEY")
        return db_value or env_value or None
    
    def get_all_settings(self) -> dict:
        rows = cur.execute("SELECT k, v FROM kv WHERE k LIKE 'setting_%'").fetchall()
        result = {}
        for k, v in rows:
            key = k.replace("setting_", "")
            # Mask encrypted values - return placeholder instead of ciphertext
            if key == "openai_api_key" and v:
                result[key] = "***MASKED***"
            elif v:
                result[key] = v
            else:
                result[key] = None
        return result

settings_service = SettingsService()
