"""
Schematic dosya okuyucu.
Desteklenen formatlar:
- .schematic (Legacy MCEdit format)
- .schem v1/v2 (Sponge Schematic)
- .schem v3 (Sponge Schematic yeni)
- .litematic (Litematica format)
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

    keys = list(root.keys()) if hasattr(root, 'keys') else []
    version = _get_int(root, "Version", 0)
    print(f"[READER] Uzantı: {suffix} | Version: {version} | Key'ler: {keys}")

    # Litematica formatı tespiti (Regions key'i var mı?)
    if "Regions" in keys:
        print("[READER] Litematica formatı tespit edildi")
        blocks = _read_litematica(root)
    elif suffix == ".schematic":
        print("[READER] Legacy MCEdit formatı")
        blocks = _read_legacy(root)
    elif suffix in (".schem", ".litematic"):
        if version >= 3:
            print("[READER] Sponge v3 formatı")
            blocks = _read_sponge_v3(root)
        elif version in (1, 2):
            print("[READER] Sponge v2 formatı")
            blocks = _read_sponge_v2(root)
        else:
            # Version yok → içeriğe bak
            if root.get("Palette"):
                print("[READER] Sponge v2 formatı (Palette bulundu)")
                blocks = _read_sponge_v2(root)
            elif root.get("Blocks"):
                print("[READER] Sponge v3 formatı (Blocks bulundu)")
                blocks = _read_sponge_v3(root)
            else:
                raise ValueError(f"Format tespit edilemedi. Key'ler: {keys}")
    else:
        raise ValueError(f"Desteklenmeyen uzantı: {suffix}")

    # Koordinat debug bilgisi
    if blocks:
        xs = [b["x"] for b in blocks]
        ys = [b["y"] for b in blocks]
        zs = [b["z"] for b in blocks]
        print(f"[READER] Blok sayısı: {len(blocks)}")
        print(f"[READER] X: {min(xs)} → {max(xs)} (genişlik: {max(xs)-min(xs)+1})")
        print(f"[READER] Y: {min(ys)} → {max(ys)} (yükseklik: {max(ys)-min(ys)+1})")
        print(f"[READER] Z: {min(zs)} → {max(zs)} (derinlik: {max(zs)-min(zs)+1})")

    return blocks


def _get_root(nbt):
    """NBT dosyasının root tag'ini döndür"""
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


def _normalize_coords(blocks: list[dict]) -> list[dict]:
    """
    Koordinatları normalize et: minimum x/y/z = 0 olsun.
    Böylece prefab her zaman 0,0,0'dan başlar.
    """
    if not blocks:
        return blocks

    min_x = min(b["x"] for b in blocks)
    min_y = min(b["y"] for b in blocks)
    min_z = min(b["z"] for b in blocks)

    # Sadece negatif veya çok büyük offset varsa normalize et
    if min_x != 0 or min_y != 0 or min_z != 0:
        print(f"[READER] Koordinatlar normalize ediliyor: offset ({min_x}, {min_y}, {min_z})")
        normalized = []
        for b in blocks:
            new_block = {
                "x": b["x"] - min_x,
                "y": b["y"] - min_y,
                "z": b["z"] - min_z,
                "name": b["name"]
            }
            # rotation varsa koru
            if "rotation" in b:
                new_block["rotation"] = b["rotation"]
            normalized.append(new_block)
        return normalized
    return blocks


# -------------------------------------------------------------------
# FORMAT 1: Legacy .schematic (MCEdit)
# -------------------------------------------------------------------
def _read_legacy(root) -> list[dict]:
    """
    Eski MCEdit .schematic formatı.
    Bloklar sayısal ID (byte array) olarak saklanır.
    Koordinat sırası: Y * (Length * Width) + Z * Width + X
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

    print(f"[READER] Legacy boyutlar: {width}x{height}x{length} (WxHxL)")

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

        # Legacy koordinat sırası: Y * (Length * Width) + Z * Width + X
        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    print(f"[READER] Legacy format okundu: {len(result)} blok (air hariç)")
    return _normalize_coords(result)


# -------------------------------------------------------------------
# FORMAT 2: Sponge v1/v2 .schem
# -------------------------------------------------------------------
def _read_sponge_v2(root) -> list[dict]:
    """
    Sponge Schematic v1/v2 formatı.
    Palette (isim→index) + BlockData (varint array) içerir.
    Koordinat sırası: (Y * length + Z) * width + X
    """
    AIR_BLOCKS = ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")

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

    print(f"[READER] Sponge v2 boyutlar: {width}x{height}x{length} (WxHxL)")

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    palette_tag = None
    for key in ["Palette", "palette"]:
        if key in root:
            palette_tag = root[key]
            break
    if palette_tag is None:
        raise ValueError("Sponge v2: 'Palette' bulunamadı")

    index_to_name: dict[int, str] = {}
    for name, idx in palette_tag.items():
        index_to_name[int(idx)] = str(name)

    block_data = None
    for key in ["BlockData", "blockData"]:
        if key in root:
            block_data = root[key]
            break
    if block_data is None:
        raise ValueError("Sponge v2: 'BlockData' bulunamadı")

    indices = _decode_varints(bytes(block_data))

    result: list[dict] = []
    for i, idx in enumerate(indices):
        name = index_to_name.get(idx, "")
        if not name or name in AIR_BLOCKS:
            continue

        # Sponge v2 koordinat sırası: (Y * length + Z) * width + X
        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    print(f"[READER] Sponge v2 format okundu: {len(result)} blok (air hariç)")
    return _normalize_coords(result)


# -------------------------------------------------------------------
# FORMAT 3: Sponge v3 .schem
# -------------------------------------------------------------------
def _read_sponge_v3(root) -> list[dict]:
    """
    Sponge Schematic v3 formatı.
    Koordinat sırası: (Y * length + Z) * width + X
    """
    AIR_BLOCKS = ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")

    blocks_section = root.get("Blocks") or root.get("blocks")

    if blocks_section is None and root.get("Palette") is not None:
        print("[READER DEBUG] v3'te Palette root'ta bulundu → v2 olarak okuyorum")
        return _read_sponge_v2(root)

    if blocks_section is None and root.get("Schematic") is not None:
        inner = root["Schematic"]
        blocks_section = inner.get("Blocks") or inner.get("blocks")
        if blocks_section is None and inner.get("Palette"):
            return _read_sponge_v2(inner)
        root = inner

    if blocks_section is None:
        keys = list(root.keys()) if hasattr(root, 'keys') else str(type(root))
        raise ValueError(f"Sponge v3: 'Blocks' section bulunamadı. Key'ler: {keys}")

    width = _get_int(root, "Width") or _get_int(root, "width")
    height = _get_int(root, "Height") or _get_int(root, "height")
    length = _get_int(root, "Length") or _get_int(root, "length")

    print(f"[READER] Sponge v3 boyutlar: {width}x{height}x{length} (WxHxL)")

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    palette_tag = None
    for key in ["Palette", "palette"]:
        if key in blocks_section:
            palette_tag = blocks_section[key]
            break
    if palette_tag is None:
        palette_tag = root.get("Palette")
    if palette_tag is None:
        raise ValueError("Sponge v3: Palette bulunamadı")

    index_to_name: dict[int, str] = {}
    for name, idx in palette_tag.items():
        index_to_name[int(idx)] = str(name)

    block_data = None
    for key in ["Data", "data", "BlockData"]:
        if key in blocks_section:
            block_data = blocks_section[key]
            break

    if block_data is None:
        keys = list(blocks_section.keys()) if hasattr(blocks_section, 'keys') else str(type(blocks_section))
        raise ValueError(f"Sponge v3: Block Data bulunamadı. Key'ler: {keys}")

    indices = _decode_varints(bytes(block_data))

    result: list[dict] = []
    for i, idx in enumerate(indices):
        name = index_to_name.get(idx, "")
        if not name or name in AIR_BLOCKS:
            continue

        # Sponge v3 koordinat sırası: (Y * length + Z) * width + X
        y = i // (width * length)
        z = (i % (width * length)) // width
        x = i % width

        result.append({"x": x, "y": y, "z": z, "name": name})

    print(f"[READER] Sponge v3 format okundu: {len(result)} blok (air hariç)")
    return _normalize_coords(result)


# -------------------------------------------------------------------
# FORMAT 4: Litematica .litematic
# -------------------------------------------------------------------
def _read_litematica(root) -> list[dict]:
    """
    Litematica .litematic formatı okuyucu.
    Regions altında packed long array ile bloklar saklanır.
    """
    regions = root.get("Regions")
    if regions is None:
        raise ValueError("Litematica: 'Regions' bulunamadı")

    all_blocks = []
    offset_x, offset_y, offset_z = 0, 0, 0

    for region_name, region in regions.items():
        print(f"[READER] Bölge okunuyor: {region_name}")
        try:
            blocks = _read_litematica_region(region, offset_x, offset_y, offset_z)
            all_blocks.extend(blocks)
            print(f"[READER] Bölge '{region_name}': {len(blocks)} blok")

            size = region.get("Size") or {}
            sx = abs(_get_int(region, "SizeX") or _get_int(size, "x", 0))
            offset_x += sx + 1
        except Exception as e:
            print(f"[READER UYARI] Bölge '{region_name}' atlandı: {e}")
            continue

    print(f"[READER] Litematica format okundu: {len(all_blocks)} blok toplam")
    return _normalize_coords(all_blocks)


def _read_litematica_region(region, off_x=0, off_y=0, off_z=0) -> list[dict]:
    """Tek bir Litematica bölgesini oku"""
    AIR_BLOCKS = ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")

    size = region.get("Size") or {}

    if hasattr(size, 'get'):
        width = abs(_get_int(size, "x", 0))
        height = abs(_get_int(size, "y", 0))
        length = abs(_get_int(size, "z", 0))
    else:
        width = height = length = 0

    if width == 0 or height == 0 or length == 0:
        try:
            if hasattr(size, '__iter__') and not hasattr(size, 'get'):
                size_list = list(size)
                if len(size_list) >= 3:
                    width = abs(int(size_list[0]))
                    height = abs(int(size_list[1]))
                    length = abs(int(size_list[2]))
        except:
            pass

    if width == 0 or height == 0 or length == 0:
        block_states = region.get("BlockStates")
        if block_states is not None:
            palette_list = region.get("BlockStatePalette") or []
            palette_size = max(len(palette_list), 1)
            bits = max(2, (palette_size - 1).bit_length())
            values_per_long = 64 // bits
            total_values = len(block_states) * values_per_long

            import math
            side = int(math.ceil(total_values ** (1/3)))
            width = height = length = side
            print(f"[READER DEBUG] Boyut tahmini: {width}x{height}x{length}")

    if width == 0 or height == 0 or length == 0:
        raise ValueError(f"Geçersiz boyutlar: {width}x{height}x{length}")

    print(f"[READER] Litematica bölge boyutlar: {width}x{height}x{length}")

    palette_list = region.get("BlockStatePalette")
    if palette_list is None:
        raise ValueError("BlockStatePalette bulunamadı")

    palette = {}
    for i, entry in enumerate(palette_list):
        if hasattr(entry, 'get'):
            name = str(entry.get("Name", "minecraft:air"))
            props = entry.get("Properties")
            if props:
                prop_str = ",".join(f"{k}={v}" for k, v in props.items())
                name = f"{name}[{prop_str}]"
        else:
            name = str(entry)
        palette[i] = name

    block_states = region.get("BlockStates")
    if block_states is None:
        raise ValueError("BlockStates bulunamadı")

    palette_size = len(palette)
    bits_per_block = max(2, (palette_size - 1).bit_length())

    total_blocks = width * height * length
    indices = _unpack_longs(list(block_states), bits_per_block, total_blocks)

    result = []

    for i in range(min(len(indices), total_blocks)):
        block_idx = indices[i]
        name = palette.get(block_idx, "minecraft:air")

        name_lower = name.lower()
        is_air = any(air in name_lower for air in ["minecraft:air", "cave_air", "void_air"])
        if is_air and "stair" not in name_lower:
            continue

        # Litematica koordinat sırası: Y * (length * width) + Z * width + X
        y = i // (length * width)
        z = (i % (length * width)) // width
        x = i % width

        result.append({
            "x": x + off_x,
            "y": y + off_y,
            "z": z + off_z,
            "name": name
        })

    return result


def _unpack_longs(long_array: list, bits: int, total: int) -> list[int]:
    """
    Minecraft packed long array'den blok indexlerini çıkar.
    """
    indices = []
    mask = (1 << bits) - 1
    values_per_long = 64 // bits

    for long_val in long_array:
        if hasattr(long_val, '__int__'):
            long_val = int(long_val)
        if long_val < 0:
            long_val += (1 << 64)

        for j in range(values_per_long):
            if len(indices) >= total:
                break
            indices.append((long_val >> (j * bits)) & mask)

        if len(indices) >= total:
            break

    return indices


def _decode_varints(data: bytes) -> list[int]:
    """
    Minecraft varint formatını decode eder.
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
