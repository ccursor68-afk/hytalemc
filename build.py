"""
Uygulamayi .exe olarak derler.
Kullanim: python build.py
"""
import subprocess
import sys
import os

def build():
    # Icon dosyasi var mi kontrol et
    if not os.path.exists("assets/icon.ico"):
        print("Icon dosyasi bulunamadi, olusturuluyor...")
        subprocess.run([sys.executable, "create_icon.py"])
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # tek exe dosyasi
        "--windowed",          # konsol penceresi acilmasin
        "--name", "HytaleConverter",
        "--icon", "assets/icon.ico",
        "--add-data", "data;data",     # Windows icin ; kullan
        "--hidden-import", "nbtlib",
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
        "--clean",
        "main.py"
    ]
    
    # Linux/Mac icin path ayiricisi
    if sys.platform != "win32":
        cmd[cmd.index("data;data")] = "data:data"
    
    print("Build basliyor...")
    print(f"Komut: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print()
        print("=" * 50)
        print("BUILD BASARILI!")
        print("=" * 50)
        if sys.platform == "win32":
            print("Exe: dist/HytaleConverter.exe")
        else:
            print("Exe: dist/HytaleConverter")
    else:
        print()
        print("BUILD BASARISIZ!")
        sys.exit(1)

if __name__ == "__main__":
    build()
