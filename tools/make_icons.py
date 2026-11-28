"""
把设计好的图标铺成 Android 各密度资源。

直接模式（推荐，素材已按规格画好，保留设计稿原始位置）：
    python tools/make_icons.py --fg foreground.png --bg background.png --legacy icon512.png

自动模式（只有一张 512 整图时，自动抠图并按 DESIGN_RATIO 反算大小）：
    python tools/make_icons.py design.png

全部输出 WebP，旧 PNG 会被清理，避免同名资源冲突。
"""

import argparse
from pathlib import Path

from PIL import Image, ImageFilter

DENSITIES = {"mdpi": 1.0, "hdpi": 1.5, "xhdpi": 2.0, "xxhdpi": 3.0, "xxxhdpi": 4.0}
LEGACY_SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
DESIGN_RATIO = 0.627  # 自动模式下，图形占可见区宽度的目标比例


def save_webp(im, path, lossless=True, quality=90):
    im.save(path, format="WEBP", lossless=lossless, quality=quality, method=6)


def place_fg(fg_img, canvas, inner_px):
    """把前景图形居中放进画布，长边限制在 inner_px。"""
    fg = fg_img.convert("RGBA")
    bbox = fg.split()[-1].point(lambda v: 255 if v > 40 else 0).getbbox()
    if bbox:
        fg = fg.crop(bbox)
    ratio = min(inner_px / fg.width, inner_px / fg.height)
    size = (max(1, round(fg.width * ratio)), max(1, round(fg.height * ratio)))
    fg = fg.resize(size, Image.LANCZOS)
    out = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    out.paste(fg, ((canvas - size[0]) // 2, (canvas - size[1]) // 2), fg)
    return out


def extract_glyph(img: Image.Image) -> Image.Image:
    """自动模式用：按与底色的距离抠图，保留柔雾边缘。"""
    im = img.convert("RGBA")
    px = im.load()
    w, h = im.size
    bg = (250, 250, 252)
    alpha = Image.new("L", (w, h), 0)
    ap = alpha.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, src_a = px[x, y]
            if src_a == 0:
                continue
            d = max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2]))
            a = int(max(0.0, min(1.0, (d - 52) / 20.0)) * 255)
            if a > 0:
                ap[x, y] = a
                op[x, y] = (r, g, b, 255)
    out.putalpha(alpha.filter(ImageFilter.GaussianBlur(0.8)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?", help="自动模式的 512 整图")
    ap.add_argument("--fg", help="前景 432px，透明底")
    ap.add_argument("--bg", help="背景 432px，不透明")
    ap.add_argument("--legacy", help="传统图标 512px，已画好圆角")
    args = ap.parse_args()

    res = Path("app/src/main/res")
    direct = bool(args.fg and args.bg)

    if direct:
        fg_src = Image.open(args.fg).convert("RGBA")
        bg_src = Image.open(args.bg).convert("RGB")
        for name, scale in DENSITIES.items():
            d = res / f"mipmap-{name}"
            d.mkdir(parents=True, exist_ok=True)
            for old in d.glob("*.png"):
                old.unlink()
            canvas = int(round(108 * scale))
            # 直接模式尊重设计稿在画布内的位置，只缩放，不重新居中
            save_webp(fg_src.resize((canvas, canvas), Image.LANCZOS), d / "ic_launcher_foreground.webp")
            # 背景是平滑渐变，无损 WebP 反而几十倍膨胀，走有损 92
            save_webp(bg_src.resize((canvas, canvas), Image.LANCZOS), d / "ic_launcher_background.webp",
                      lossless=False, quality=92)
        print("前景背景已按密度铺开，位置沿用设计稿")
    else:
        if not args.source:
            print("缺参数：--fg/--bg，或一个 source")
            return 1
        src = Image.open(args.source).convert("RGBA")
        if src.size != (512, 512):
            src = src.resize((512, 512), Image.LANCZOS)
        glyph = extract_glyph(src)
        bbox = glyph.split()[-1].point(lambda v: 255 if v > 96 else 0).getbbox()
        pad = 10
        crop = glyph.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                           min(512, bbox[2] + pad), min(512, bbox[3] + pad)))
        for name, scale in DENSITIES.items():
            d = res / f"mipmap-{name}"
            d.mkdir(parents=True, exist_ok=True)
            for old in d.glob("*.png"):
                old.unlink()
            canvas = int(round(108 * scale))
            inner = int(round(canvas * (72 / 108) * DESIGN_RATIO * crop.width / (bbox[2] - bbox[0])))
            save_webp(place_fg(crop, canvas, inner), d / "ic_launcher_foreground.webp")

    legacy = Image.open(args.legacy or args.source).convert("RGBA")
    for name, scale in DENSITIES.items():
        save_webp(legacy.resize((LEGACY_SIZES[name],) * 2, Image.LANCZOS),
                  res / f"mipmap-{name}" / "ic_launcher.webp", lossless=False, quality=92)

    splash = res / "drawable-nodpi"
    splash.mkdir(parents=True, exist_ok=True)
    save_webp(legacy.resize((360, 360), Image.LANCZOS), splash / "ic_splash.webp",
              lossless=False, quality=90)

    anydpi = res / "mipmap-anydpi-v26"
    anydpi.mkdir(parents=True, exist_ok=True)
    bg_ref = "@mipmap/ic_launcher_background" if direct else "@drawable/ic_launcher_background"
    (anydpi / "ic_launcher.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        f'    <background android:drawable="{bg_ref}" />\n'
        '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
        "</adaptive-icon>\n",
        encoding="utf-8",
    )
    if direct:
        (res / "drawable" / "ic_launcher_background.xml").unlink(missing_ok=True)

    (res / "values" / "colors.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        '    <color name="ic_launcher_background">#F5F7FA</color>\n'
        '    <color name="window_bg">#FFFFFF</color>\n'
        "</resources>\n",
        encoding="utf-8",
    )

    total = sum(p.stat().st_size for p in res.rglob("*.webp"))
    print(f"完成，图片合计 {total:,} 字节 ({total/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
