from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.settings_service import settings_service

router = APIRouter()

class SettingIn(BaseModel):
    key: str
    value: str

class LMStudioConfigIn(BaseModel):
    base_url: str

class OpenAIConfigIn(BaseModel):
    api_key: str

@router.get("")
def get_all_settings():
    """Get all settings with API keys masked"""
    return settings_service.get_all_settings()

@router.post("/lmstudio")
def set_lmstudio_config(config: LMStudioConfigIn):
    """Configure LM Studio endpoint URL"""
    if not config.base_url:
        raise HTTPException(status_code=400, detail="base_url is required")
    
    if not (config.base_url.startswith("http://") or config.base_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="base_url must start with http:// or https://")
    
    settings_service.set_setting("lmstudio_url", config.base_url.rstrip("/"))
    return {"status": "ok", "lmstudio_url": config.base_url}

@router.post("/openai")
def set_openai_config(config: OpenAIConfigIn):
    """Configure OpenAI API key (encrypted at rest)"""
    if not config.api_key:
        raise HTTPException(status_code=400, detail="api_key is required")
    
    if not config.api_key.startswith("sk-"):
        raise HTTPException(status_code=400, detail="Invalid OpenAI API key format")
    
    settings_service.set_setting("openai_api_key", config.api_key, encrypted=True)
    return {"status": "ok", "api_key": "***MASKED***"}

@router.delete("/lmstudio")
def delete_lmstudio_config():
    """Remove LM Studio configuration (will fall back to env/defaults)"""
    settings_service.delete_setting("lmstudio_url")
    return {"status": "ok"}

@router.delete("/openai")
def delete_openai_config():
    """Remove OpenAI API key (will fall back to env var if set)"""
    settings_service.delete_setting("openai_api_key")
    return {"status": "ok"}

@router.get("/current")
def get_current_config():
    """Get current effective configuration (with masking)"""
    try:
        lmstudio_url = settings_service.get_lmstudio_url()
    except Exception:
        lmstudio_url = "http://localhost:1234/v1"
    
    try:
        has_api_key = bool(settings_service.get_openai_api_key())
    except Exception:
        has_api_key = False
    
    return {
        "lmstudio_url": lmstudio_url,
        "openai_api_key": "***SET***" if has_api_key else None,
    }
