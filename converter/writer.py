"""Hytale prefab dosyası yazıcısı."""

import json
from pathlib import Path


def write_prefab(blocks: list[dict], output_path: Path) -> None:
    """
    Hytale prefab formatinda dosya yazar.

    blocks: [{"x": int, "y": int, "z": int, "name": str}, ...]
    """
    # Boş name, None, ve "air" içerenleri filtrele
    clean_blocks = [
        b for b in blocks 
        if b is not None 
        and b.get("name", "") != ""
        and "air" not in b.get("name", "").lower()
    ]
    
    print(f"[WRITER] Toplam blok: {len(blocks)}, Filtre sonrası: {len(clean_blocks)}")
    
    if len(clean_blocks) == 0:
        print("[WRITER UYARI] Hiç geçerli blok yok! Prefab boş olacak.")
    else:
        # İlk 3 bloğu debug için göster
        print("[WRITER] Örnek bloklar:")
        for b in clean_blocks[:3]:
            print(f"  - {b}")
    
    prefab = {
        "version": 8,
        "blockIdVersion": 10,
        "anchorX": 0,
        "anchorY": 0,
        "anchorZ": 0,
        "blocks": clean_blocks,
        "fluids": [],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(prefab, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    
    print(f"[WRITER] Prefab yazıldı: {output_path} ({len(clean_blocks)} blok)")
