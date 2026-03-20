"""Minecraft bloklarini Hytale prefab bloklarina esler."""

import json
from pathlib import Path

BLOCK_MAP_PATH = Path(__file__).resolve().parent.parent / "data" / "block_map.json"
FALLBACK_BLOCK = "Rock_Stone_Brick"

# Minecraft yön -> Hytale rotation eşleştirmesi
# Minecraft: north=0, south=2, west=1, east=3, up=1, down=0
# Hytale rotation: 0, 1, 2, 3 (90 derece döndürme)
FACING_TO_ROTATION = {
    "north": 0,
    "south": 2,
    "east": 1,
    "west": 3,
    "up": 0,
    "down": 0,
}

# Minecraft axis -> Hytale rotation
AXIS_TO_ROTATION = {
    "y": 0,
    "x": 1,
    "z": 2,
}


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
        
        return mapping

    def _clean_name(self, name: str) -> str:
        """Blok adindaki property kismini temizleyip normalize eder."""
        # "minecraft:oak_log[axis=y]" -> "minecraft:oak_log"
        name = name.split("[")[0]
        return name.lower().strip()

    def _extract_rotation(self, minecraft_name: str) -> int | None:
        """Minecraft blok state'inden rotation değerini çıkarır."""
        # "minecraft:oak_stairs[facing=north,half=bottom]" formatından rotation çıkar
        if "[" not in minecraft_name:
            return None
        
        try:
            props_str = minecraft_name.split("[")[1].rstrip("]")
            props = {}
            for prop in props_str.split(","):
                if "=" in prop:
                    key, value = prop.split("=", 1)
                    props[key.strip()] = value.strip()
            
            # facing property varsa
            if "facing" in props:
                return FACING_TO_ROTATION.get(props["facing"], 0)
            
            # axis property varsa (log blokları için)
            if "axis" in props:
                return AXIS_TO_ROTATION.get(props["axis"], 0)
            
            # half property varsa (slab'lar için)
            if "half" in props:
                if props["half"] == "top":
                    return 8  # Hytale'de top slab rotation=8
                    
            # type property varsa (slab'lar için)
            if "type" in props:
                if props["type"] == "top":
                    return 8
                    
        except Exception:
            pass
        
        return None

    def map_block(self, minecraft_name: str, x: int, y: int, z: int) -> dict | None:
        """
        Minecraft blok adini Hytale adina cevirir.
        None donerse bu blok prefab'a yazilmaz.
        """
        clean_name = self._clean_name(minecraft_name)
        hytale_name = self.mapping.get(clean_name)
        rotation = self._extract_rotation(minecraft_name)

        # DEBUG: ilk 20 blok eslemesini konsola yazdirir.
        if self._debug_count < 20:
            rot_str = f" rot={rotation}" if rotation is not None else ""
            print(f"[MAPPER DEBUG] raw='{minecraft_name}' -> '{hytale_name}'{rot_str}")
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

        result = {"x": x, "y": y, "z": z, "name": hytale_name}
        
        # Rotation varsa ekle
        if rotation is not None:
            result["rotation"] = rotation
        
        return result

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
