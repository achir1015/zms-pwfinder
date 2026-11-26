"""產生 app 圖示 PNG/ICO（資料助秘 密碼查找器：藍紫底、放大鏡、鑰匙孔）。"""
import os
import sys

# Windows CI 的 stdout 被導向時預設 cp1252，印中文會 UnicodeEncodeError，先轉 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "web", "assets")
os.makedirs(OUT, exist_ok=True)


def draw(size=512):
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 圓角底（漸層以兩色疊近似）
    r = int(s * 0.2)
    d.rounded_rectangle([int(s*0.05), int(s*0.05), int(s*0.95), int(s*0.95)],
                        radius=r, fill=(47, 109, 240, 255))
    d.rounded_rectangle([int(s*0.05), int(s*0.05), int(s*0.95), int(s*0.55)],
                        radius=r, fill=(79, 70, 229, 90))
    # 放大鏡圈
    cx, cy, rad = int(s*0.42), int(s*0.42), int(s*0.2)
    w = max(6, int(s*0.06))
    d.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], outline=(255, 255, 255, 255), width=w)
    # 握把
    d.line([int(s*0.57), int(s*0.57), int(s*0.75), int(s*0.75)],
           fill=(255, 255, 255, 255), width=int(s*0.08))
    # 鑰匙孔（黃）
    kr = int(s*0.06)
    d.ellipse([cx-kr, cy-kr-int(s*0.03), cx+kr, cy+kr-int(s*0.03)], fill=(255, 213, 74, 255))
    d.polygon([(cx-int(s*0.03), cy+int(s*0.01)), (cx+int(s*0.03), cy+int(s*0.01)),
               (cx+int(s*0.018), cy+int(s*0.12)), (cx-int(s*0.018), cy+int(s*0.12))],
              fill=(255, 213, 74, 255))
    return img


base = draw(512)
base.save(os.path.join(OUT, "icon.png"))
# ICO 多尺寸（給 Windows 視窗、捷徑、打包）
base.save(os.path.join(OUT, "icon.ico"),
          sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
# PWA / 手機圖示
for sz in (180, 192, 512):
    base.resize((sz, sz)).save(os.path.join(OUT, f"icon-{sz}.png"))
# maskable（四周留白，避免被圓角裁掉）
mask = Image.new("RGBA", (512, 512), (47, 109, 240, 255))
inner = draw(512).resize((360, 360))
mask.paste(inner, (76, 76), inner)
mask.save(os.path.join(OUT, "icon-maskable.png"))
print("icon.png/ico 與 PWA 圖示（180/192/512/maskable）已產生於", OUT)
