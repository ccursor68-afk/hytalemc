"""Uygulama giriş noktası."""

import json
from pathlib import Path

from gui.app import HytaleConverterApp


def main() -> None:
    """GUI uygulamasını başlatır."""
    block_map_path = Path(__file__).resolve().parent / "data" / "block_map.json"
    with block_map_path.open("r", encoding="utf-8") as f:
        bm = json.load(f)
    real_keys = {k: v for k, v in bm.items() if not k.startswith("_")}
    print(f"[STARTUP] block_map.json yüklendi: {len(real_keys)} blok")
    print(f"[STARTUP] Ornek: minecraft:dirt -> {real_keys.get('minecraft:dirt')}")
    print(f"[STARTUP] Ornek: minecraft:oak_log -> {real_keys.get('minecraft:oak_log')}")

    app = HytaleConverterApp()
    app.run()


if __name__ == "__main__":
    main()
