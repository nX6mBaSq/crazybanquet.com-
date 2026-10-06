"""サイト表示用の画像を uploads/ の元画像から生成する。

使い方（リポジトリのルートで実行）:
    pip install pillow   # Pillow 11.2 以上（AVIF 対応）
    python tools/build-images.py

出演者写真を追加するときは:
  1. 元画像を uploads/<名前>.webp として置く（1:1 なら 1080×1080、16:9 なら 1920×1080 推奨）
  2. このスクリプトを実行 → uploads/resized/<名前>-360/-640 の .avif / .webp ができる
     （16:9 など横長の写真は -1080 も生成）
  3. index.html の LINE UP に、既存の出演者と同じ <picture> を追加する
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "uploads"
OUT = SRC / "resized"

BG = (10, 14, 20, 255)  # サイトの背景色 #0A0E14

# 正方形の写真として扱わないファイル
NON_PHOTOS = {"logo-landscape.png", "favicon.png", "video-poster.jpg"}


def save_pair(img, stem, webp_q, avif_q):
    img.save(OUT / f"{stem}.webp", "WEBP", quality=webp_q, method=6)
    img.save(OUT / f"{stem}.avif", "AVIF", quality=avif_q, speed=4)


def resize_w(img, w):
    return img.resize((w, round(w * img.height / img.width)), Image.LANCZOS)


def build_photos():
    for path in sorted(SRC.glob("*.webp")):
        if path.name in NON_PHOTOS:
            continue
        img = Image.open(path).convert("RGB")
        # 16:9 などの横長写真は全幅（SPECIAL GUEST）で使うため 1080px も用意
        widths = (360, 640) if img.width == img.height else (360, 640, 1080)
        for w in widths:
            save_pair(resize_w(img, w), f"{path.stem}-{w}", webp_q=80, avif_q=60)
        print("photo :", path.name)


def build_logo():
    img = Image.open(SRC / "logo-landscape.png").convert("RGBA")
    for w in (640, 960):
        save_pair(resize_w(img, w), f"logo-{w}", webp_q=85, avif_q=70)
    print("logo  : logo-landscape.png")


def build_poster():
    img = Image.open(SRC / "video-poster.jpg").convert("RGB")
    for w in (760, 1280):
        save_pair(resize_w(img, w), f"video-poster-{w}", webp_q=78, avif_q=55)
    print("poster: video-poster.jpg")


def build_icons():
    icon = Image.open(SRC / "favicon.png").convert("RGBA")
    resize_w(icon, 48).save(SRC / "favicon-48.png", optimize=True)
    resize_w(icon, 192).save(SRC / "favicon-192.png", optimize=True)
    # iOS のホーム画面用：透過部分は黒く塗られるので、背景色と余白をつけて書き出す
    touch = Image.new("RGBA", (180, 180), BG)
    mark = resize_w(icon, 148)
    touch.alpha_composite(mark, ((180 - mark.width) // 2, (180 - mark.height) // 2))
    touch.convert("RGB").save(SRC / "apple-touch-icon.png", optimize=True)
    print("icons : favicon-48 / favicon-192 / apple-touch-icon")


def build_ogp():
    w, h = 1200, 630
    ogp = Image.new("RGBA", (w, h), BG)
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    from PIL import ImageDraw

    d = ImageDraw.Draw(grid)
    for x in range(0, w, 40):
        d.line([(x, 0), (x, h)], fill=(0, 194, 255, 22))
    for y in range(0, h, 40):
        d.line([(0, y), (w, y)], fill=(57, 255, 143, 22))
    ogp.alpha_composite(grid)
    logo = resize_w(Image.open(SRC / "logo-landscape.png").convert("RGBA"), 900)
    ogp.alpha_composite(logo, ((w - logo.width) // 2, (h - logo.height) // 2))
    ogp.convert("RGB").save(SRC / "ogp.jpg", "JPEG", quality=88, optimize=True)
    print("ogp   : ogp.jpg")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build_photos()
    build_logo()
    build_poster()
    build_icons()
    build_ogp()
