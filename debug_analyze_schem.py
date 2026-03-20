from collections import Counter
from pathlib import Path

from converter.mapper import BlockMapper
from converter.reader import read_schematic


def main() -> None:
    p = Path(r"C:\Users\UNLOST\Downloads\28513.schem")
    print("[FILE]", p.name)
    blocks = read_schematic(p)
    print("[BLOCKS_TOTAL]", len(blocks))

    raw = Counter([b.get("name", "") for b in blocks])
    print("[TOP_RAW]")
    for k, v in raw.most_common(20):
        print(f"{k} => {v}")

    m = BlockMapper()
    mapped: list[str] = []
    none_count = 0
    fallback_count = 0

    for b in blocks:
        clean = m._clean_name(str(b.get("name", "")))
        r = m.mapping.get(clean)
        if r is None:
            fallback_count += 1
            r = "Rock_Stone_Brick"
        elif r == "":
            none_count += 1
            continue
        mapped.append(r)

    mc = Counter(mapped)
    print("[TOP_MAPPED]")
    for k, v in mc.most_common(20):
        print(f"{k} => {v}")

    print(
        "[STATS] mapped=",
        len(mapped),
        "skipped_empty=",
        none_count,
        "fallback=",
        fallback_count,
    )


if __name__ == "__main__":
    main()
