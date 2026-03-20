"""
Hytale Converter - Minecraft schematic dosyalarini Hytale prefab formatina donusturur.

Kullanim:
    python main.py          # GUI baslat
    python main.py --help   # Yardim
"""

import sys
import os


def resource_path(relative_path: str) -> str:
    """PyInstaller icin kaynak dosya yolu"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def main():
    """Ana fonksiyon"""
    # GUI'yi baslat
    try:
        from gui.app import run
        run()
    except ImportError as e:
        print(f"GUI baslatma hatasi: {e}")
        print("Gerekli kutuphaneler yukleniyor...")
        os.system(f"{sys.executable} -m pip install customtkinter")
        
        # Tekrar dene
        from gui.app import run
        run()
    except Exception as e:
        print(f"Hata: {e}")
        import traceback
        traceback.print_exc()
        input("Devam etmek icin Enter'a basin...")


if __name__ == "__main__":
    main()
