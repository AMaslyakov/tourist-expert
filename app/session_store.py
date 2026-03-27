from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def get_consultation_dir() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    consultation_dir = project_root / "consultation"
    consultation_dir.mkdir(parents=True, exist_ok=True)
    return consultation_dir


def save_consultation_session(payload: dict[str, Any]) -> Path:
    consultation_dir = get_consultation_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    file_path = consultation_dir / f"consultation_{timestamp}_{uuid4().hex[:8]}.json"
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return file_path
