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
        size_x, size_y, size_z = 1, 1, 1
    else:
        # İlk 3 bloğu debug için göster
        print("[WRITER] Örnek bloklar:")
        for b in clean_blocks[:3]:
            print(f"  - {b}")
        
        # Boyut hesaplaması (bounding box)
        xs = [b['x'] for b in clean_blocks]
        ys = [b['y'] for b in clean_blocks]
        zs = [b['z'] for b in clean_blocks]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
        
        size_x = max_x - min_x + 1
        size_y = max_y - min_y + 1
        size_z = max_z - min_z + 1
        
        print(f"[WRITER] Boyut: {size_x}x{size_y}x{size_z}")
    
    # Hytale prefab formatına çevir
    # Format: {"x": int, "y": int, "z": int, "name": str, "rotation"?: int, "support"?: int}
    hytale_blocks = []
    for b in clean_blocks:
        block_entry = {
            "x": b['x'],
            "y": b['y'], 
            "z": b['z'],
            "name": b['name']
        }
        # rotation varsa ekle
        if 'rotation' in b:
            block_entry['rotation'] = b['rotation']
        # support varsa ekle (yaprak blokları için)
        if 'support' in b:
            block_entry['support'] = b['support']
        hytale_blocks.append(block_entry)
    
    prefab = {
        "version": 8,
        "blockIdVersion": 10,
        "anchorX": 0,
        "anchorY": 0,
        "anchorZ": 0,
        "blocks": hytale_blocks,
        "fluids": []
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(prefab, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    
    print(f"[WRITER] Prefab yazıldı: {output_path} ({len(hytale_blocks)} blok)")
