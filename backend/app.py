import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from main_minimal import app


def _env_bool(name: str, default: bool = False) -> bool:
    value = (os.getenv(name, "") or "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "y", "on"}

if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", "8002"))
        log_level = (os.getenv("UVICORN_LOG_LEVEL", "info") or "info").strip().lower()
        access_log = _env_bool("UVICORN_ACCESS_LOG", True)
        debug = _env_bool("DEBUG", False)

        if debug:
            # Raise verbosity automatically when DEBUG=1 unless explicitly overridden.
            log_level = (os.getenv("UVICORN_LOG_LEVEL", "debug") or "debug").strip().lower()

        print(
            f"Starting API on 0.0.0.0:{port} | "
            f"log_level={log_level} | access_log={access_log} | debug={debug}"
        )

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level=log_level,
            access_log=access_log,
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
