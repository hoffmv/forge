import subprocess
import httpx
from backend.utils.logger import log, log_action, log_error

VRAM_MODEL_PRIORITY = [
    {"min_vram_gb": 48, "preferred_contains": ["70b"], "reason": "Large reasoning model"},
    {"min_vram_gb": 24, "preferred_contains": ["32b", "30b"], "reason": "Full-size coder"},
    {"min_vram_gb": 16, "preferred_contains": ["14b", "13b", "20b"], "reason": "Mid-range coder"},
    {"min_vram_gb": 8,  "preferred_contains": ["7b", "8b"], "reason": "Efficient coder"},
]


def _query_vram() -> dict:
    """Run nvidia-smi and return total and free VRAM in GB."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            log_error("vram", f"nvidia-smi failed: {result.stderr.strip()}")
            return {"total_gb": None, "free_gb": None}

        lines = result.stdout.strip().split("\n")
        if not lines:
            return {"total_gb": None, "free_gb": None}

        # Parse "total_mb, free_mb" from first GPU
        parts = lines[0].split(",")
        total_mb = float(parts[0].strip())
        free_mb = float(parts[1].strip())
        total_gb = round(total_mb / 1024.0, 1)
        free_gb = round(free_mb / 1024.0, 1)
        log_action("vram", f"Total VRAM: {total_gb} GB, Free: {free_gb} GB")
        return {"total_gb": total_gb, "free_gb": free_gb}

    except FileNotFoundError:
        log("nvidia-smi not found — no NVIDIA GPU or drivers not installed", "warning")
        return {"total_gb": None, "free_gb": None}
    except Exception as e:
        log_error("vram", str(e))
        return {"total_gb": None, "free_gb": None}


def get_loaded_models(lm_studio_url: str) -> list[str]:
    """GET /v1/models from LM Studio and return list of model IDs."""
    try:
        resp = httpx.get(f"{lm_studio_url}/models", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = [m["id"] for m in data.get("data", [])]
        log_action("models", f"LM Studio reports {len(models)} loaded model(s)", {"models": models})
        return models
    except httpx.ConnectError:
        log_error("models", f"Cannot connect to LM Studio at {lm_studio_url}")
        return []
    except Exception as e:
        log_error("models", str(e))
        return []


def select_model(lm_studio_url: str) -> dict:
    """
    Auto-select the best model based on total VRAM capacity and loaded models.

    Uses TOTAL VRAM (not free) for tier selection because free VRAM fluctuates
    based on which models are currently loaded — total capacity is the stable
    indicator of what the machine can handle.

    Returns:
        {"model": str | None, "total_vram_gb": float | None, "vram_free_gb": float | None, "reason": str}
    """
    vram = _query_vram()
    total_gb = vram["total_gb"]
    free_gb = vram["free_gb"]
    models = get_loaded_models(lm_studio_url)

    if not models:
        log("No models loaded in LM Studio", "warning")
        return {"model": None, "total_vram_gb": total_gb, "vram_free_gb": free_gb, "reason": "No models loaded in LM Studio"}

    # Use TOTAL VRAM to determine which tier this machine supports.
    # Keywords are ordered by preference — iterate keywords first so
    # e.g. "32b" models are picked before "30b" models in the same tier.
    if total_gb is not None:
        for tier in VRAM_MODEL_PRIORITY:
            if total_gb >= tier["min_vram_gb"]:
                for keyword in tier["preferred_contains"]:
                    for model_id in models:
                        if keyword in model_id.lower():
                            reason = f"{tier['reason']} (Total VRAM: {total_gb} GB, matched '{keyword}' in '{model_id}')"
                            log_action("model_select", reason)
                            return {"model": model_id, "total_vram_gb": total_gb, "vram_free_gb": free_gb, "reason": reason}

    # Fallback: return first loaded model
    fallback = models[0]
    reason = f"Fallback — using first loaded model '{fallback}'"
    if total_gb is not None:
        reason += f" (Total VRAM: {total_gb} GB, no tier match)"
    else:
        reason += " (VRAM detection unavailable)"

    log(reason, "warning")
    return {"model": fallback, "total_vram_gb": total_gb, "vram_free_gb": free_gb, "reason": reason}
