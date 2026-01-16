from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterable, List


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def is_cjk_char(char: str) -> bool:
    if not char:
        return False
    code = ord(char)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0x20000 <= code <= 0x2A6DF
        or 0x2A700 <= code <= 0x2B73F
        or 0x2B740 <= code <= 0x2B81F
        or 0x2B820 <= code <= 0x2CEAF
    )


def split_sentence(sentence: str) -> List[str]:
    return [char for char in sentence if is_cjk_char(char)]


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def write_concat_list(audio_paths: Iterable[Path], output_path: Path) -> None:
    ensure_parent(output_path)
    lines = [f"file '{path.as_posix()}'" for path in audio_paths]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def expand_user(path: str | Path) -> Path:
    return Path(os.path.expanduser(str(path))).resolve()
