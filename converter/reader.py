"""
Schematic dosya okuyucu.
Desteklenen formatlar:
- .schematic (Legacy MCEdit format)
- .schem v1/v2 (Sponge Schematic)
- .schem v3 (Sponge Schematic yeni)
"""

from __future__ import annotations

import nbtlib
from pathlib import Path


def read_schematic(file_path: Path) -> list[dict]:
    """
    Herhangi bir schematic dosyasını okur.
    Döndürür: [{"x": int, "y": int, "z": int, "name": "minecraft:stone"}, ...]
    """
    suffix = file_path.suffix.lower()

    try:
        nbt = nbtlib.load(str(file_path))
    except Exception as e:
        raise ValueError(f"NBT okunamadı: {e}")

    root = _get_root(nbt)

    # Tüm root key'lerini logla (debug)
    try:
        print(f"[READER DEBUG] Root key'ler: {list(root.keys())}")
    except:
        pass

    version = _get_int(root, "Version", 0)
    print(f"[READER DEBUG] Format: {suffix}, Version: {version}")

    if suffix == ".schematic":
        return _read_legacy(root)
    elif suffix in (".schem", ".litematic"):
        if version >= 3:
            print("[READER DEBUG] Sponge v3 formatı deneniyor")
            return _read_sponge_v3(root)
        elif version == 2 or version == 1:
            print("[READER DEBUG] Sponge v2 formatı deneniyor")
            return _read_sponge_v2(root)
        else:
            # Version yoksa içeriğe bak
            if root.get("Palette"):
                print("[READER DEBUG] Version yok, Palette var → v2 deneniyor")
                return _read_sponge_v2(root)
            elif root.get("Blocks"):
                print("[READER DEBUG] Version yok, Blocks var → v3 deneniyor")
                return _read_sponge_v3(root)
            else:
                raise ValueError(f"Format tespit edilemedi. Key'ler: {list(root.keys())}")
    else:
        raise ValueError(f"Desteklenmeyen uzantı: {suffix}")


def _get_root(nbt):
    """NBT dosyasının root tag'ini döndür"""
    # nbtlib bazen root'u direkt, bazen wrapper içinde verir
    if "" in nbt:
        return nbt[""]
    if "Schematic" in nbt:
        return nbt["Schematic"]
    return nbt


def _get_int(tag, key, default=0):
    """NBT tag'den güvenli int okuma"""
    try:
        val = tag.get(key, default)
        return int(val)
    except Exception:
        return default


# -------------------------------------------------------------------
# FORMAT 1: Legacy .schematic (MCEdit)
# -------------------------------------------------------------------
def _read_legacy(root) -> list[dict]:
    """
    Eski MCEdit .schematic formatı.
    Bloklar sayısal ID (byte array) olarak saklanır.
    """
    LEGACY_IDS = {
        0: "",
        1: "minecraft:stone",
        2: "minecraft:grass_block",
        3: "minecraft:dirt",
        4: "minecraft:cobblestone",
        5: "minecraft:oak_planks",
        7: "minecraft:bedrock",
        8: "minecraft:water",
        9: "minecraft:water",
        12: "minecraft:sand",
        13: "minecraft:gravel",
        14: "minecraft:gold_ore",
        15: "minecraft:iron_ore",
        16: "minecraft:coal_ore",
        17: "minecraft:oak_log",
        18: "minecraft:oak_leaves",
        20: "minecraft:glass",
        21: "minecraft:lapis_ore",
        22: "minecraft:lapis_block",
        24: "minecraft:sandstone",
        35: "minecraft:white_wool",
        41: "minecraft:gold_block",
        42: "minecraft:iron_block",
        45: "minecraft:bricks",
        47: "minecraft:bookshelf",
        48: "minecraft:mossy_cobblestone",
        49: "minecraft:obsidian",
        53: "minecraft:oak_stairs",
        56: "minecraft:diamond_ore",
        57: "minecraft:diamond_block",
        73: "minecraft:redstone_ore",
        78: "minecraft:snow",
        79: "minecraft:ice",
        80: "minecraft:snow_block",
        82: "minecraft:clay",
        85: "minecraft:oak_fence",
        87: "minecraft:netherrack",
        88: "minecraft:soul_sand",
        89: "minecraft:glowstone",
        95: "minecraft:glass",
        98: "minecraft:stone_bricks",
        101: "minecraft:iron_bars",
        102: "minecraft:glass",
        106: "minecraft:vine",
        108: "minecraft:bricks",
        109: "minecraft:stone_bricks",
        110: "minecraft:mycelium",
        111: "minecraft:lily_pad",
        112: "minecraft:nether_bricks",
        121: "minecraft:end_stone",
        123: "minecraft:glowstone",
        128: "minecraft:sandstone",
        129: "minecraft:emerald_ore",
        133: "minecraft:emerald_block",
        139: "minecraft:cobblestone_wall",
        155: "minecraft:quartz_block",
        159: "minecraft:terracotta",
        161: "minecraft:oak_leaves",
        162: "minecraft:oak_log",
        168: "minecraft:prismarine",
        169: "minecraft:glowstone",
        170: "minecraft:hay_block",
        172: "minecraft:terracotta",
        173: "minecraft:coal_block",
        174: "minecraft:packed_ice",
        179: "minecraft:red_sandstone",
        251: "minecraft:white_concrete",
    }

    width = _get_int(root, "Width")
    height = _get_int(root, "Height")
    length = _get_int(root, "Length")

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    blocks_raw = root.get("Blocks")
    if blocks_raw is None:
        raise ValueError("Legacy format: 'Blocks' array bulunamadı")

    add_raw = root.get("AddBlocks")

    result: list[dict] = []
    for i, byte_val in enumerate(blocks_raw):
        block_id = byte_val & 0xFF
        if add_raw and i // 2 < len(add_raw):
            nibble = add_raw[i // 2] & 0xFF
            if i % 2 == 0:
                block_id += (nibble & 0x0F) << 8
            else:
                block_id += (nibble & 0xF0) << 4

        name = LEGACY_IDS.get(block_id, "")
        if not name:
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    print(f"[READER] Legacy format okundu: {len(result)} blok (air hariç)")
    return result


# -------------------------------------------------------------------
# FORMAT 2: Sponge v1/v2 .schem
# -------------------------------------------------------------------
def _read_sponge_v2(root) -> list[dict]:
    """
    Sponge Schematic v1/v2 formatı.
    Palette (isim→index) + BlockData (varint array) içerir.
    """
    # Air blok isimleri - stairs hariç tutulmalı (st-air-s false positive)
    AIR_BLOCKS = ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")
    
    # Boyutlar - farklı key isimleri olabilir
    width = (
        _get_int(root, "Width")
        or _get_int(root, "width")
        or _get_int(root.get("Metadata", {}), "Width", 0)
    )
    height = (
        _get_int(root, "Height")
        or _get_int(root, "height")
        or _get_int(root.get("Metadata", {}), "Height", 0)
    )
    length = (
        _get_int(root, "Length")
        or _get_int(root, "length")
        or _get_int(root.get("Metadata", {}), "Length", 0)
    )

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    # Palette: {"minecraft:stone": 0, "minecraft:air": 1, ...}
    palette_tag = root.get("Palette")
    if palette_tag is None:
        palette_tag = root.get("palette")
    if palette_tag is None:
        raise ValueError("Sponge v2: 'Palette' bulunamadı")

    # Palette'i {index: name} formatına çevir
    index_to_name: dict[int, str] = {}
    for name, idx in palette_tag.items():
        index_to_name[int(idx)] = str(name)

    # BlockData: varint encoded byte array
    block_data = root.get("BlockData")
    if block_data is None:
        block_data = root.get("blockData")
    if block_data is None:
        raise ValueError("Sponge v2: 'BlockData' bulunamadı")

    # Varint decode
    indices = _decode_varints(bytes(block_data))

    result: list[dict] = []
    for i, idx in enumerate(indices):
        name = index_to_name.get(idx, "")
        if not name or name in AIR_BLOCKS:
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    print(f"[READER] Sponge v2 format okundu: {len(result)} blok (air hariç)")
    # İlk 5 bloğu debug için göster
    for b in result[:5]:
        print(f"[READER DEBUG] Örnek blok: {b}")
    return result


# -------------------------------------------------------------------
# FORMAT 3: Sponge v3 .schem
# -------------------------------------------------------------------
def _read_sponge_v3(root) -> list[dict]:
    """
    Sponge Schematic v3 — birden fazla yapıyı dene.
    """
    # Air blok isimleri - stairs hariç tutulmalı (st-air-s false positive)
    AIR_BLOCKS = ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")

    # DENEME 1: Standart v3 — "Blocks" altında Palette + Data
    blocks_section = root.get("Blocks")

    # DENEME 2: Bazı araçlar "blocks" (küçük harf) yazar
    if blocks_section is None:
        blocks_section = root.get("blocks")

    # DENEME 3: Bazı v3 dosyaları Palette'i direkt root'ta tutar (v2 gibi)
    if blocks_section is None and root.get("Palette") is not None:
        print("[READER DEBUG] v3'te Palette root'ta bulundu → v2 olarak okuyorum")
        return _read_sponge_v2(root)

    # DENEME 4: "Schematic" wrapper içinde
    if blocks_section is None and root.get("Schematic") is not None:
        inner = root["Schematic"]
        blocks_section = inner.get("Blocks") or inner.get("blocks")
        if blocks_section is None and inner.get("Palette"):
            print("[READER DEBUG] Schematic wrapper içinde Palette bulundu → v2 olarak okuyorum")
            return _read_sponge_v2(inner)
        root = inner  # boyutlar da inner'da

    if blocks_section is None:
        # Son çare: tüm key'leri logla ve daha iyi hata ver
        keys = list(root.keys()) if hasattr(root, 'keys') else str(type(root))
        raise ValueError(
            f"Sponge v3: 'Blocks' section bulunamadı. "
            f"Mevcut key'ler: {keys}"
        )

    # Boyutlar
    width = _get_int(root, "Width") or _get_int(root, "width")
    height = _get_int(root, "Height") or _get_int(root, "height")
    length = _get_int(root, "Length") or _get_int(root, "length")

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    # Palette
    palette_tag = (
        blocks_section.get("Palette") or
        blocks_section.get("palette") or
        root.get("Palette")
    )
    if palette_tag is None:
        raise ValueError("Sponge v3: Palette bulunamadı")

    index_to_name: dict[int, str] = {}
    for name, idx in palette_tag.items():
        index_to_name[int(idx)] = str(name)

    # Block data
    block_data = None
    for key in ["Data", "data", "BlockData"]:
        if key in blocks_section:
            block_data = blocks_section[key]
            break
    
    if block_data is None:
        keys = list(blocks_section.keys()) if hasattr(blocks_section, 'keys') else str(type(blocks_section))
        raise ValueError(f"Sponge v3: Block Data bulunamadı. Blocks key'leri: {keys}")

    indices = _decode_varints(bytes(block_data))

    result: list[dict] = []
    for i, idx in enumerate(indices):
        name = index_to_name.get(idx, "")
        if not name or name in AIR_BLOCKS:
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    print(f"[READER] Sponge v3 format okundu: {len(result)} blok (air hariç)")
    # İlk 5 bloğu debug için göster
    for b in result[:5]:
        print(f"[READER DEBUG] Örnek blok: {b}")
    return result


# -------------------------------------------------------------------
# YARDIMCI: Varint decoder
# -------------------------------------------------------------------
def _decode_varints(data: bytes) -> list[int]:
    """
    Minecraft varint formatını decode eder.
    Her sayı 1-5 byte arası, MSB devam bitini gösterir.
    """
    result: list[int] = []
    i = 0
    while i < len(data):
        value = 0
        shift = 0
        while True:
            if i >= len(data):
                break
            byte_val = data[i]
            i += 1
            value |= (byte_val & 0x7F) << shift
            shift += 7
            if not (byte_val & 0x80):
                break
        result.append(value)
    return result
