import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

def get_data_dir():
    """Get the application data directory (writable location)"""
    forge_data = os.getenv("FORGE_DATA_DIR")
    if forge_data:
        return Path(forge_data)
    
    # Use AppData on Windows, ~/.forge on Unix
    if os.name == 'nt':
        appdata = os.getenv('APPDATA') or os.path.expanduser('~')
        data_dir = Path(appdata) / 'FORGE'
    else:
        data_dir = Path.home() / '.forge'
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

class Settings(BaseSettings):
    MODE: str = "LOCAL"
    LLM_PROVIDER: str = "AUTO"

    LMSTUDIO_BASE_URL: str = "http://localhost:1234/v1"
    LMSTUDIO_MODEL: str = "gpt-oss-20b"

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    WORKSPACE_ROOT: str = str(get_data_dir() / "workspaces")
    DB_PATH: str = str(get_data_dir() / "builder.db")
    MAX_ITERS: int = 3

    MAX_INPUT_CHARS: int = 120_000
    MAX_REPLY_TOKENS: int = 2048

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
