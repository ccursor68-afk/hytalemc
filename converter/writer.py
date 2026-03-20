import json
from pathlib import Path


def write_prefab(blocks: list[dict], output_path: Path) -> None:
    """
    Hytale prefab formatinda dosya yazar.

    blocks: [{"x": int, "y": int, "z": int, "name": str}, ...]
    """
    prefab = {
        "version": 8,
        "blockIdVersion": 10,
        "anchorX": 0,
        "anchorY": 0,
        "anchorZ": 0,
        "blocks": blocks,
        "fluids": [],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(prefab, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
