# Minecraft -> Hytale Schematic Converter

CustomTkinter tabanli masaustu uygulamasi ile `.schematic`, `.schem` ve `.litematic` dosyalarini toplu sekilde Hytale `prefab.json` formatina cevirir.

## Ozellikler

- Coklu dosya secimi ile toplu donusum
- Klasor secip desteklenen tum dosyalari otomatik bulma
- Sol panelde kuyruk yonetimi (secileni kaldir / tumunu temizle)
- Her dosya icin ayri durum ikonu ve progress
- Genel donusum progress bar
- Arka planda thread ile donusum (GUI donmaz)
- Ayarlar paneli:
  - Cikti klasoru secimi
  - Ciktiyi kaynak dosyayla ayni klasore yazma
  - Eslesmeyen bloklar icin strict mode
- Sonuc raporu (basarili/hatali sayisi, hata listesi)
- Raporu `.txt` olarak kaydetme
- `amulet-core` deneme + `nbtlib` fallback mekanizmasi

## Kurulum

```bash
pip install -r requirements.txt
python main.py
```

Windows'ta `amulet-core` kurulumu hata verirse uygulama `nbtlib` fallback ile yine calisir.

## Test Dosyalari Uretme

Ilk calistirma sonrasi ornek dosya seti olusturmak icin:

```bash
python create_test_files.py
```

Bu komut `test_files/` klasoru altina 3 adet ornek `.schem` dosyasi uretir.

## Proje Yapisi

```text
hytale-converter/
├── main.py
├── gui/
│   ├── __init__.py
│   ├── app.py
│   └── components.py
├── converter/
│   ├── __init__.py
│   ├── reader.py
│   ├── mapper.py
│   └── writer.py
├── data/
│   └── block_map.json
├── create_test_files.py
├── requirements.txt
└── README.md
```

## Notlar

- Varsayilan tema dark mode'dur.
- Eslesmeyen bloklar strict mode kapaliyken `hytale:stone` ile fallback edilir.
- Bozuk veya okunamayan NBT dosyalari yalnizca ilgili dosya icin hata olarak isaretlenir, kuyruktaki diger dosyalar devam eder.
