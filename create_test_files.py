"""Ornek test schematic dosyalari olusturma araci."""

from __future__ import annotations

from pathlib import Path

import nbtlib
from nbtlib import ByteArray, Compound, Int, List, Short, String


def create_simple_schem(path: Path, name: str, width: int, height: int, length: int) -> None:
    """Temel bir Sponge .schem dosyasi olusturur."""
    total = width * height * length

    # Palette: 0 air, 1 stone, 2 dirt, 3 grass.
    palette = Compound(
        {
            "minecraft:air": Int(0),
            "minecraft:stone": Int(1),
            "minecraft:dirt": Int(2),
            "minecraft:grass_block": Int(3),
        }
    )

    block_data = []
    for i in range(total):
        # Katmanlara gore ornek bir dagilim olusturulur.
        y = i // (width * length)
        if y == 0:
            block_data.append(1)
        elif y == 1:
            block_data.append(2)
        elif y == 2:
            block_data.append(3)
        else:
            block_data.append(0)

    root = Compound(
        {
            "Version": Int(2),
            "DataVersion": Int(3120),
            "Width": Short(width),
            "Height": Short(height),
            "Length": Short(length),
            "PaletteMax": Int(4),
            "Palette": palette,
            "BlockData": ByteArray(block_data),
            "Metadata": Compound({"Name": String(name)}),
            "BlockEntities": List[Compound]([]),
            "Entities": List[Compound]([]),
            "Offset": List[Int]([Int(0), Int(0), Int(0)]),
        }
    )

    file = nbtlib.File(root)
    file.save(str(path), gzipped=True)


def main() -> None:
    """3 adet ornek .schem dosyasi olusturur."""
    out_dir = Path(__file__).resolve().parent / "test_files"
    out_dir.mkdir(parents=True, exist_ok=True)

    create_simple_schem(out_dir / "test_house.schem", "test_house", 10, 6, 10)
    create_simple_schem(out_dir / "test_tower.schem", "test_tower", 7, 14, 7)
    create_simple_schem(out_dir / "test_platform.schem", "test_platform", 16, 4, 16)

    print(f"Test dosyalari olusturuldu: {out_dir}")


if __name__ == "__main__":
    main()
