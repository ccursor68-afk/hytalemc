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

    # Root key'i bul (bazen "" bazen "Schematic" bazen başka bir şey)
    root = _get_root(nbt)

    if suffix == ".schematic":
        return _read_legacy(root)
    elif suffix in (".schem", ".litematic"):
        # Sponge versiyonunu tespit et
        version = _get_int(root, "Version", 1)
        if version >= 3:
            return _read_sponge_v3(root)
        else:
            return _read_sponge_v2(root)
    else:
        # Uzantı bilinmiyor, içeriğe bakarak tahmin et
        if "Palette" in root:
            return _read_sponge_v2(root)
        blocks_val = root.get("Blocks")
        if "Blocks" in root and isinstance(blocks_val, nbtlib.ByteArray):
            return _read_legacy(root)
        raise ValueError("Desteklenmeyen format")


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

    return result


# -------------------------------------------------------------------
# FORMAT 2: Sponge v1/v2 .schem
# -------------------------------------------------------------------
def _read_sponge_v2(root) -> list[dict]:
    """
    Sponge Schematic v1/v2 formatı.
    Palette (isim→index) + BlockData (varint array) içerir.
    """
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
        if not name or name in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air"):
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    return result


# -------------------------------------------------------------------
# FORMAT 3: Sponge v3 .schem
# -------------------------------------------------------------------
def _read_sponge_v3(root) -> list[dict]:
    """
    Sponge Schematic v3 formatı.
    Blocks altında Palette + Data içerir.
    """
    # v3'te veriler "Blocks" key'i altında
    blocks_section = root.get("Blocks")
    if blocks_section is None:
        raise ValueError("Sponge v3: 'Blocks' section bulunamadı")

    # Boyutlar root'ta
    width = _get_int(root, "Width")
    height = _get_int(root, "Height")
    length = _get_int(root, "Length")

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    palette_tag = blocks_section.get("Palette")
    if palette_tag is None:
        raise ValueError("Sponge v3: Blocks.Palette bulunamadı")

    index_to_name: dict[int, str] = {}
    for name, idx in palette_tag.items():
        index_to_name[int(idx)] = str(name)

    block_data = blocks_section.get("Data")
    if block_data is None:
        raise ValueError("Sponge v3: Blocks.Data bulunamadı")

    indices = _decode_varints(bytes(block_data))

    result: list[dict] = []
    for i, idx in enumerate(indices):
        name = index_to_name.get(idx, "")
        if not name or "air" in name:
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

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

"""
Schematic dosya okuyucu.
Desteklenen formatlar:
- .schematic (Legacy MCEdit format)
- .schem v1/v2 (Sponge Schematic)
- .schem v3 (Sponge Schematic yeni)
"""

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

    # Root key'i bul (bazen "" bazen "Schematic" bazen başka bir şey)
    root = _get_root(nbt)

    if suffix == ".schematic":
        return _read_legacy(root)
    elif suffix in (".schem", ".litematic"):
        # Sponge versiyonunu tespit et
        version = _get_int(root, "Version", 1)
        if version >= 3:
            return _read_sponge_v3(root)
        else:
            return _read_sponge_v2(root)
    else:
        # Uzantı bilinmiyor, içeriğe bakarak tahmin et
        if "Palette" in root:
            return _read_sponge_v2(root)
        elif "Blocks" in root and isinstance(root.get("Blocks"), nbtlib.ByteArray):
            return _read_legacy(root)
        else:
            raise ValueError("Desteklenmeyen format")


def _get_root(nbt):
    """NBT dosyasının root tag'ini döndür"""
    # nbtlib bazen root'u direkt, bazen wrapper içinde verir
    if "" in nbt:
        root = nbt[""]
    elif "Schematic" in nbt:
        root = nbt["Schematic"]
    else:
        root = nbt
    return root


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

    return result


# -------------------------------------------------------------------
# FORMAT 2: Sponge v1/v2 .schem
# -------------------------------------------------------------------
def _read_sponge_v2(root) -> list[dict]:
    """
    Sponge Schematic v1/v2 formatı.
    Palette (isim→index) + BlockData (varint array) içerir.
    """
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
        if not name or name in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air"):
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    return result


# -------------------------------------------------------------------
# FORMAT 3: Sponge v3 .schem
# -------------------------------------------------------------------
def _read_sponge_v3(root) -> list[dict]:
    """
    Sponge Schematic v3 formatı.
    Blocks altında Palette + Data içerir.
    """
    # v3'te veriler "Blocks" key'i altında
    blocks_section = root.get("Blocks")
    if blocks_section is None:
        raise ValueError("Sponge v3: 'Blocks' section bulunamadı")

    # Boyutlar root'ta
    width = _get_int(root, "Width")
    height = _get_int(root, "Height")
    length = _get_int(root, "Length")

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    palette_tag = blocks_section.get("Palette")
    if palette_tag is None:
        raise ValueError("Sponge v3: Blocks.Palette bulunamadı")

    index_to_name: dict[int, str] = {}
    for name, idx in palette_tag.items():
        index_to_name[int(idx)] = str(name)

    block_data = blocks_section.get("Data")
    if block_data is None:
        raise ValueError("Sponge v3: Blocks.Data bulunamadı")

    indices = _decode_varints(bytes(block_data))

    result: list[dict] = []
    for i, idx in enumerate(indices):
        name = index_to_name.get(idx, "")
        if not name or "air" in name:
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

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

"""
Schematic dosya okuyucu.
Desteklenen formatlar:
- .schematic (Legacy MCEdit format)
- .schem v1/v2 (Sponge Schematic)
- .schem v3 (Sponge Schematic yeni)
"""

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

    # Root key'i bul (bazen "" bazen "Schematic" bazen başka bir şey)
    root = _get_root(nbt)

    if suffix == ".schematic":
        return _read_legacy(root)
    elif suffix in (".schem", ".litematic"):
        # Sponge versiyonunu tespit et
        version = _get_int(root, "Version", 1)
        if version >= 3:
            return _read_sponge_v3(root)
        else:
            return _read_sponge_v2(root)
    else:
        # Uzantı bilinmiyor, içeriğe bakarak tahmin et
        if "Palette" in root:
            return _read_sponge_v2(root)
        elif "Blocks" in root and isinstance(root.get("Blocks"), nbtlib.ByteArray):
            return _read_legacy(root)
        else:
            raise ValueError("Desteklenmeyen format")


def _get_root(nbt):
    """NBT dosyasının root tag'ini döndür"""
    # nbtlib bazen root'u direkt, bazen wrapper içinde verir
    if "" in nbt:
        root = nbt[""]
    elif "Schematic" in nbt:
        root = nbt["Schematic"]
    else:
        root = nbt
    return root


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

    return result


# -------------------------------------------------------------------
# FORMAT 2: Sponge v1/v2 .schem
# -------------------------------------------------------------------
def _read_sponge_v2(root) -> list[dict]:
    """
    Sponge Schematic v1/v2 formatı.
    Palette (isim→index) + BlockData (varint array) içerir.
    """
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
        if not name or name in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air"):
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    return result


# -------------------------------------------------------------------
# FORMAT 3: Sponge v3 .schem
# -------------------------------------------------------------------
def _read_sponge_v3(root) -> list[dict]:
    """
    Sponge Schematic v3 formatı.
    Blocks altında Palette + Data içerir.
    """
    # v3'te veriler "Blocks" key'i altında
    blocks_section = root.get("Blocks")
    if blocks_section is None:
        raise ValueError("Sponge v3: 'Blocks' section bulunamadı")

    # Boyutlar root'ta
    width = _get_int(root, "Width")
    height = _get_int(root, "Height")
    length = _get_int(root, "Length")

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    palette_tag = blocks_section.get("Palette")
    if palette_tag is None:
        raise ValueError("Sponge v3: Blocks.Palette bulunamadı")

    index_to_name: dict[int, str] = {}
    for name, idx in palette_tag.items():
        index_to_name[int(idx)] = str(name)

    block_data = blocks_section.get("Data")
    if block_data is None:
        raise ValueError("Sponge v3: Blocks.Data bulunamadı")

    indices = _decode_varints(bytes(block_data))

    result: list[dict] = []
    for i, idx in enumerate(indices):
        name = index_to_name.get(idx, "")
        if not name or "air" in name:
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

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

"""
Schematic dosya okuyucu.
Desteklenen formatlar:
- .schematic (Legacy MCEdit format)
- .schem v1/v2 (Sponge Schematic)
- .schem v3 (Sponge Schematic yeni)
"""

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

    # Root key'i bul (bazen "" bazen "Schematic" bazen başka bir şey)
    root = _get_root(nbt)

    if suffix == ".schematic":
        return _read_legacy(root)
    elif suffix in (".schem", ".litematic"):
        # Sponge versiyonunu tespit et
        version = _get_int(root, "Version", 1)
        if version >= 3:
            return _read_sponge_v3(root)
        else:
            return _read_sponge_v2(root)
    else:
        # Uzantı bilinmiyor, içeriğe bakarak tahmin et
        if "Palette" in root:
            return _read_sponge_v2(root)
        elif "Blocks" in root and isinstance(root.get("Blocks"), nbtlib.ByteArray):
            return _read_legacy(root)
        else:
            raise ValueError("Desteklenmeyen format")


def _get_root(nbt):
    """NBT dosyasının root tag'ini döndür"""
    # nbtlib bazen root'u direkt, bazen wrapper içinde verir
    if "" in nbt:
        root = nbt[""]
    elif "Schematic" in nbt:
        root = nbt["Schematic"]
    else:
        root = nbt
    return root


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

    return result


# -------------------------------------------------------------------
# FORMAT 2: Sponge v1/v2 .schem
# -------------------------------------------------------------------
def _read_sponge_v2(root) -> list[dict]:
    """
    Sponge Schematic v1/v2 formatı.
    Palette (isim→index) + BlockData (varint array) içerir.
    """
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
        if not name or name in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air"):
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    return result


# -------------------------------------------------------------------
# FORMAT 3: Sponge v3 .schem
# -------------------------------------------------------------------
def _read_sponge_v3(root) -> list[dict]:
    """
    Sponge Schematic v3 formatı.
    Blocks altında Palette + Data içerir.
    """
    # v3'te veriler "Blocks" key'i altında
    blocks_section = root.get("Blocks")
    if blocks_section is None:
        raise ValueError("Sponge v3: 'Blocks' section bulunamadı")

    # Boyutlar root'ta
    width = _get_int(root, "Width")
    height = _get_int(root, "Height")
    length = _get_int(root, "Length")

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    palette_tag = blocks_section.get("Palette")
    if palette_tag is None:
        raise ValueError("Sponge v3: Blocks.Palette bulunamadı")

    index_to_name: dict[int, str] = {}
    for name, idx in palette_tag.items():
        index_to_name[int(idx)] = str(name)

    block_data = blocks_section.get("Data")
    if block_data is None:
        raise ValueError("Sponge v3: Blocks.Data bulunamadı")

    indices = _decode_varints(bytes(block_data))

    result: list[dict] = []
    for i, idx in enumerate(indices):
        name = index_to_name.get(idx, "")
        if not name or "air" in name:
            continue

        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

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

"""Minecraft schematic dosyalarini okuma islemleri."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import nbtlib

try:
    # Amulet bazi ortamlarda kurulamayabildigi icin opsiyonel tutulur.
    import amulet  # type: ignore

    AMULET_AVAILABLE = True
except Exception:
    AMULET_AVAILABLE = False


SUPPORTED_EXTENSIONS = {".schematic", ".schem", ".litematic"}


class SchematicReadError(Exception):
    """Schematic okuma sirasinda olusan hatalari temsil eder."""


@dataclass(slots=True)
class BlockRecord:
    """Tek bir blok konumu ve Minecraft block id bilgisini tutar."""

    x: int
    y: int
    z: int
    block_id: str


@dataclass(slots=True)
class StructureData:
    """Okunan yapinin boyut ve blok listesini tutar."""

    name: str
    size_x: int
    size_y: int
    size_z: int
    blocks: list[BlockRecord]


class SchematicReader:
    """Schematic dosyalarini amulet/nbtlib ile okur."""

    def read_file(self, file_path: Path) -> StructureData:
        """Dosya uzantisina gore uygun okuyucuyu secerek veriyi doner."""
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise SchematicReadError(f"Desteklenmeyen dosya uzantisi: {suffix}")

        # Once amulet ile dene, hata olursa nbtlib fallback kullan.
        if AMULET_AVAILABLE:
            try:
                data = self._read_with_amulet(file_path)
                if data is not None:
                    return data
            except Exception:
                # Fallback mekanizmasi: amulet basarisizsa nbtlib devam eder.
                pass

        try:
            nbt = nbtlib.load(str(file_path))
        except Exception as exc:
            raise SchematicReadError(f"NBT verisi okunamadi: {exc}") from exc

        if suffix == ".schem":
            return self._read_sponge_schem(file_path, nbt)
        if suffix == ".schematic":
            return self._read_classic_schematic(file_path, nbt)
        return self._read_litematic(file_path, nbt)

    def _get_nbt_root(self, nbt_obj: Any) -> Any:
        """nbtlib surum farklarina gore root compound nesnesini doner."""
        # Bazi surumlerde nbtlib.load File objesi (root attr ile), bazilarinda
        # dogrudan Compound benzeri bir obje donebilir.
        if hasattr(nbt_obj, "root"):
            return nbt_obj.root
        return nbt_obj

    def _read_with_amulet(self, file_path: Path) -> StructureData | None:
        """Amulet kullanan basit bir okuma denemesi yapar, uygun degilse None doner."""
        # Amulet API surumlere gore degisebildigi icin bu bolum korumali yazildi.
        try:
            level = amulet.load_level(str(file_path))  # type: ignore[attr-defined]
        except Exception:
            return None

        try:
            bounds = level.bounds("main")  # type: ignore[attr-defined]
            min_x, min_y, min_z = bounds.min_x, bounds.min_y, bounds.min_z
            max_x, max_y, max_z = bounds.max_x, bounds.max_y, bounds.max_z
            blocks: list[BlockRecord] = []
            for x in range(min_x, max_x):
                for y in range(min_y, max_y):
                    for z in range(min_z, max_z):
                        block, _ = level.get_version_block(x, y, z, "java", (1, 20, 4))  # type: ignore[attr-defined]
                        if str(block.namespaced_name) != "minecraft:air":
                            blocks.append(
                                BlockRecord(
                                    x=x - min_x,
                                    y=y - min_y,
                                    z=z - min_z,
                                    block_id=str(block.namespaced_name),
                                )
                            )
            return StructureData(
                name=file_path.stem,
                size_x=max_x - min_x,
                size_y=max_y - min_y,
                size_z=max_z - min_z,
                blocks=blocks,
            )
        except Exception:
            return None
        finally:
            try:
                level.close()  # type: ignore[attr-defined]
            except Exception:
                pass

    def _read_sponge_schem(self, file_path: Path, nbt: nbtlib.File) -> StructureData:
        """Sponge .schem formatini okuyup blok listesine cevirir."""
        root = self._get_nbt_root(nbt)
        try:
            width = int(root["Width"])
            height = int(root["Height"])
            length = int(root["Length"])
            palette_compound = root["Palette"]
            block_data = root["BlockData"]
        except Exception as exc:
            raise SchematicReadError(f"Hatali .schem formati: {exc}") from exc

        # Palette degerlerini tersleyip index->block map uretilir.
        index_to_block: dict[int, str] = {}
        for block_name, palette_index in palette_compound.items():
            index_to_block[int(palette_index)] = str(block_name)

        blocks: list[BlockRecord] = []
        for i, state_index in enumerate(block_data):
            block_id = index_to_block.get(int(state_index), "minecraft:air")
            if block_id == "minecraft:air":
                continue
            x = i % width
            z = (i // width) % length
            y = i // (width * length)
            blocks.append(BlockRecord(x=x, y=y, z=z, block_id=block_id))

        return StructureData(
            name=file_path.stem,
            size_x=width,
            size_y=height,
            size_z=length,
            blocks=blocks,
        )

    def _read_classic_schematic(self, file_path: Path, nbt: nbtlib.File) -> StructureData:
        """Klasik .schematic formatini okuyup blok listesi olusturur."""
        root = self._get_nbt_root(nbt)
        try:
            width = int(root["Width"])
            height = int(root["Height"])
            length = int(root["Length"])
            blocks_arr = root["Blocks"]
        except Exception as exc:
            raise SchematicReadError(f"Hatali .schematic formati: {exc}") from exc

        numeric_to_name = self._legacy_numeric_map()
        blocks: list[BlockRecord] = []
        total = width * height * length
        for i in range(min(total, len(blocks_arr))):
            numeric_id = int(blocks_arr[i])
            block_id = numeric_to_name.get(numeric_id, "minecraft:air")
            if block_id == "minecraft:air":
                continue
            x = i % width
            z = (i // width) % length
            y = i // (width * length)
            blocks.append(BlockRecord(x=x, y=y, z=z, block_id=block_id))

        return StructureData(
            name=file_path.stem,
            size_x=width,
            size_y=height,
            size_z=length,
            blocks=blocks,
        )

    def _read_litematic(self, file_path: Path, nbt: nbtlib.File) -> StructureData:
        """Litematic formatini temel seviyede okuyup bloklari cikartir."""
        root = self._get_nbt_root(nbt)
        regions = root.get("Regions")
        if not regions:
            raise SchematicReadError("Litematic icinde Regions verisi bulunamadi.")

        # Ilk region kullanilir; birden cok region destegi sonra genisletilebilir.
        region_name = next(iter(regions.keys()))
        region = regions[region_name]

        try:
            size = region["Size"]
            width = abs(int(size["x"]))
            height = abs(int(size["y"]))
            length = abs(int(size["z"]))
            palette = region["BlockStatePalette"]
            block_states = region["BlockStates"]
        except Exception as exc:
            raise SchematicReadError(f"Hatali .litematic formati: {exc}") from exc

        palette_ids: list[str] = []
        for palette_entry in palette:
            name = str(palette_entry.get("Name", "minecraft:air"))
            palette_ids.append(name)

        # Litematic bit-packed dizisini acmak karmasik oldugu icin burada sade bir cozum var:
        # Eger tum state dizisi sayisal olarak alinabiliyorsa dogrudan index kabul edilir.
        state_values: list[int] = []
        for val in block_states:
            state_values.append(int(val))

        blocks: list[BlockRecord] = []
        total = width * height * length
        for i in range(min(total, len(state_values))):
            palette_index = state_values[i]
            block_id = palette_ids[palette_index] if 0 <= palette_index < len(palette_ids) else "minecraft:air"
            if block_id == "minecraft:air":
                continue
            x = i % width
            z = (i // width) % length
            y = i // (width * length)
            blocks.append(BlockRecord(x=x, y=y, z=z, block_id=block_id))

        return StructureData(
            name=file_path.stem,
            size_x=width,
            size_y=height,
            size_z=length,
            blocks=blocks,
        )

    def _legacy_numeric_map(self) -> dict[int, str]:
        """Klasik schematic icin temel numeric-id -> namespaced map doner."""
        return {
            0: "minecraft:air",
            1: "minecraft:stone",
            2: "minecraft:grass_block",
            3: "minecraft:dirt",
            4: "minecraft:cobblestone",
            5: "minecraft:oak_planks",
            8: "minecraft:water",
            9: "minecraft:water",
            12: "minecraft:sand",
            13: "minecraft:gravel",
            17: "minecraft:oak_log",
            20: "minecraft:glass",
            24: "minecraft:sandstone",
            35: "minecraft:white_wool",
            41: "minecraft:gold_block",
            42: "minecraft:iron_block",
            45: "minecraft:bricks",
            48: "minecraft:mossy_cobblestone",
            49: "minecraft:obsidian",
            57: "minecraft:diamond_block",
            98: "minecraft:stone_bricks",
        }
