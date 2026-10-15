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
NON_PHOTOS = {"logo-landscape-volume5.png", "favicon.png", "video-poster.jpg"}
# OGP の元画像は photo/ogp.jpg（正方形のフライヤー）。差し替えたらこのスクリプトを実行する


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
    img = Image.open(SRC / "logo-landscape-volume5.png").convert("RGBA")
    for w in (640, 960):
        save_pair(resize_w(img, w), f"logo-{w}", webp_q=85, avif_q=70)
    print("logo  : logo-landscape-volume5.png")


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
    """photo/ogp.jpg（正方形のフライヤー）から SNS シェア用と検索用の画像を作る。

    - uploads/ogp.jpg   : 1200×630。SNS は横長に切り抜くため、フライヤー全体を中央に置き、
                          左右はフライヤーをぼかして暗くした背景で埋める
    - uploads/flyer.jpg : 1200×1200。Google のイベント表示用（構造化データの 1:1 画像）
    """
    from PIL import ImageEnhance, ImageFilter

    flyer = Image.open(ROOT / "photo" / "ogp.jpg").convert("RGB")
    w, h = 1200, 630

    bg = flyer.resize((w, round(w * flyer.height / flyer.width)), Image.LANCZOS)
    top = (bg.height - h) // 2
    bg = bg.crop((0, top, w, top + h)).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)

    fg = flyer.resize((round(h * flyer.width / flyer.height), h), Image.LANCZOS)
    bg.paste(fg, ((w - fg.width) // 2, 0))
    bg.save(SRC / "ogp.jpg", "JPEG", quality=88, optimize=True, progressive=True)

    flyer.resize((1200, 1200), Image.LANCZOS).save(
        SRC / "flyer.jpg", "JPEG", quality=85, optimize=True, progressive=True
    )
    print("ogp   : ogp.jpg / flyer.jpg")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build_photos()
    build_logo()
    build_poster()
    build_icons()
    build_ogp()
