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
        self._debug_count = 0
        self._unmapped_blocks: set[str] = set()

    def _load_map(self) -> dict[str, str]:
        """Block map dosyasini okuyup meta key'leri filtreleyerek doner."""
        if not BLOCK_MAP_PATH.exists():
            print(f"[MAPPER HATA] block_map.json bulunamadı: {BLOCK_MAP_PATH.absolute()}")
            return {}
        
        try:
            with open(BLOCK_MAP_PATH, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            print(f"[MAPPER HATA] block_map.json okunamadı: {e}")
            return {}
        
        # _ ile baslayan anahtarlar metadata oldugu icin map disinda tutulur.
        mapping = {k: v for k, v in raw.items() if not k.startswith("_")}
        print(f"[MAPPER] block_map.json yüklendi: {len(mapping)} blok tanımı")
        
        # Örnek eşlemeleri göster
        test_keys = ["minecraft:stone", "minecraft:dirt", "minecraft:oak_log", "minecraft:cobblestone"]
        for key in test_keys:
            if key in mapping:
                print(f"[MAPPER] Örnek: '{key}' -> '{mapping[key]}'")
        
        return mapping

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
        if self._debug_count < 20:
            print(f"[MAPPER DEBUG] raw='{minecraft_name}' clean='{clean_name}' result='{hytale_name}'")
            self._debug_count += 1

        if hytale_name is None:
            # Bilinmeyen bloklarda fallback kullanilir ve loglanır.
            if clean_name not in self._unmapped_blocks:
                self._unmapped_blocks.add(clean_name)
                if len(self._unmapped_blocks) <= 20:
                    print(f"[MAPPER UYARI] Eşleşme bulunamadı: '{clean_name}' -> fallback '{FALLBACK_BLOCK}'")
            hytale_name = FALLBACK_BLOCK

        if hytale_name == "":
            # Bos mapping degeri "yazma/atla" demektir (air, torch vb.).
            return None

        return {"x": x, "y": y, "z": z, "name": hytale_name}

    def map_blocks(self, blocks: list[dict]) -> list[dict]:
        """Blok listesini prefab'in bekledigi x,y,z,name formatina donusturur."""
        print(f"[MAPPER] Gelen blok sayısı: {len(blocks)}")
        
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
        
        print(f"[MAPPER] Dönüştürülen blok sayısı: {len(result)} (air ve boş eşleşmeler çıkarıldı)")
        
        if self._unmapped_blocks:
            print(f"[MAPPER] Toplam {len(self._unmapped_blocks)} farklı blok fallback kullandı")
        
        # Reset debug counter for next conversion
        self._debug_count = 0
        self._unmapped_blocks.clear()
        
        return result
