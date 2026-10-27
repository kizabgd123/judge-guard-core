import os
from typing import Optional


def safe_load_dotenv(dotenv_path: Optional[str] = ".env") -> None:
    """
    Safely load environment variables from a .env file.
    Tries python-dotenv first; if not installed or fails, falls back to a clean internal parser.

    Args:
        dotenv_path: Path to the environment file. Defaults to `.env`; relative paths
            resolve against the current working directory.

    Returns:
        None.
    """
    if dotenv_path is None:
        dotenv_path = ".env"
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
        return
    except Exception:
        pass

    # Fallback to current dir or parent dir if .env not in exact path
    candidates = [dotenv_path, os.path.join(os.getcwd(), ".env")]
    target = None
    for cand in candidates:
        if os.path.exists(cand):
            target = cand
            break

    if not target:
        return

    try:
        with open(target, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                if k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass
