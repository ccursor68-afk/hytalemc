"""
Uygulama ikonu oluşturur.
Kullanım: python create_icon.py
"""
from PIL import Image, ImageDraw
import os
import math

os.makedirs("assets", exist_ok=True)

# 256x256 ikon
img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Arka plan - koyu mavi
draw.rounded_rectangle([8, 8, 248, 248], radius=40, fill="#0d1117")

# Dış altıgen (Hytale teması)
cx, cy, r = 128, 128, 90
hex_points = []
for i in range(6):
    angle = math.radians(60 * i - 30)
    hex_points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
draw.polygon(hex_points, outline="#0066cc", width=6)

# İç altıgen
r2 = 55
hex2 = []
for i in range(6):
    angle = math.radians(60 * i - 30)
    hex2.append((cx + r2 * math.cos(angle), cy + r2 * math.sin(angle)))
draw.polygon(hex2, fill="#002a60", outline="#0055cc", width=3)

# Ok işareti (play/convert sembolü)
draw.polygon([(108, 100), (108, 156), (158, 128)], fill="#66aaff")

# Farklı boyutlar için resize
sizes = [16, 32, 48, 64, 128, 256]
imgs = [img.resize((s, s), Image.LANCZOS) for s in sizes]
imgs[0].save(
    "assets/icon.ico",
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=imgs[1:]
)

print("assets/icon.ico olusturuldu")
