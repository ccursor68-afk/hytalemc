"""Minecraft bloklarini Hytale prefab bloklarina esler."""

import json
from pathlib import Path

BLOCK_MAP_PATH = Path(__file__).resolve().parent.parent / "data" / "block_map.json"
FALLBACK_BLOCK = "Rock_Stone_Brick"


class BlockMapper:
    """Minecraft blok adlarini Hytale isimlerine cevirir."""

    def __init__(self) -> None:
        """Block mapping tablosunu JSON dosyasindan yukler."""
        self.mapping = self._load_map()

    def _load_map(self) -> dict[str, str]:
        """Block map dosyasini okuyup meta key'leri filtreleyerek doner."""
        with open(BLOCK_MAP_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        # _ ile baslayan anahtarlar metadata oldugu icin map disinda tutulur.
        return {k: v for k, v in raw.items() if not k.startswith("_")}

    def _clean_name(self, name: str) -> str:
        """Blok adindaki property kismini temizleyip normalize eder."""
        # "minecraft:oak_log[axis=y]" -> "minecraft:oak_log"
        name = name.split("[")[0]
        return name.lower().strip()

    def map_block(self, minecraft_name: str, x: int, y: int, z: int) -> dict | None:
        """
        Minecraft blok adini Hytale adina cevirir.
        None donerse bu blok prefab'a yazilmaz.
        """
        clean_name = self._clean_name(minecraft_name)
        hytale_name = self.mapping.get(clean_name)

        # DEBUG: ilk 20 blok eslemesini konsola yazdirir.
        if not hasattr(self, "_debug_count"):
            self._debug_count = 0
        if self._debug_count < 20:
            print(f"[DEBUG] '{clean_name}' -> '{hytale_name}'")
            self._debug_count += 1

        if hytale_name is None:
            # Bilinmeyen bloklarda fallback kullanilir.
            hytale_name = FALLBACK_BLOCK

        if hytale_name == "":
            # Bos mapping degeri "yazma/atla" demektir.
            return None

        return {"x": x, "y": y, "z": z, "name": hytale_name}

    def map_blocks(self, blocks: list[dict]) -> list[dict]:
        """Blok listesini prefab'in bekledigi x,y,z,name formatina donusturur."""
        result: list[dict] = []
        for block in blocks:
            mapped = self.map_block(
                str(block.get("name", "")),
                int(block.get("x", 0)),
                int(block.get("y", 0)),
                int(block.get("z", 0)),
            )
            if mapped is not None:
                result.append(mapped)
        return result
